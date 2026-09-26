@bot.message_handler(commands=['video', 'omni'])
def create_video(message):
    prompt = message.text.replace('/video', '').replace('/omni', '').strip()
    if not prompt:
        bot.reply_to(message, "⚠️ Напиши промпт:\n`/video sports car drifting at high speed, neon rain`", parse_mode='Markdown')
        return

    status_msg = bot.reply_to(message, "🎬 Генерация видео запущена (Fal GPU)... Ожидание около 30–50 сек.")

    submit_url = "https://queue.fal.run/fal-ai/ltx-video"
    headers = {
        "Authorization": f"Key {FAL_KEY}",
        "Content-Type": "application/json"
    }
    payload = json.dumps({"prompt": prompt}).encode('utf-8')

    temp_file = f"video_{message.chat.id}.mp4"
    try:
        req = urllib.request.Request(submit_url, data=payload, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            submit_res = json.loads(resp.read().decode('utf-8'))

        status_url = submit_res.get("status_url")
        response_url = submit_res.get("response_url")

        video_url = None
        for _ in range(50):
            time.sleep(3)
            check_req = urllib.request.Request(status_url, headers=headers)
            with urllib.request.urlopen(check_req, timeout=30) as check_resp:
                check_data = json.loads(check_resp.read().decode('utf-8'))
                if check_data.get("status") == "COMPLETED":
                    res_req = urllib.request.Request(response_url, headers=headers)
                    with urllib.request.urlopen(res_req, timeout=30) as r_resp:
                        final_data = json.loads(r_resp.read().decode('utf-8'))
                        video_obj = final_data.get("video")
                        if isinstance(video_obj, dict):
                            video_url = video_obj.get("url")
                        elif isinstance(video_obj, str):
                            video_url = video_obj
                    break

        if not video_url:
            bot.reply_to(message, "❌ Таймаут очереди. Попробуй ещё раз.")
            return

        req_dl = urllib.request.Request(video_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req_dl, timeout=120) as v_resp, open(temp_file, 'wb') as f:
            f.write(v_resp.read())

        with open(temp_file, 'rb') as vf:
            bot.send_video(
                message.chat.id,
                video=vf,
                caption=f"🎬 **Результат:**\n{prompt}",
                supports_streaming=True,
                parse_mode='Markdown'
            )

        try:
            bot.delete_message(message.chat.id, status_msg.message_id)
        except Exception:
            pass

    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, f"❌ Ошибка генерации: {e}")

    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)
