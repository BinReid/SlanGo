let mediaRecorder;
    let audioChunks = [];
    let isRecording = false;
    let recordingTimer;
    let recordingSeconds = 0;

    // Элементы DOM
    const recordButton = document.getElementById('record-button');
    const recordingStatus = document.getElementById('recording-status');
    const recordingTimerEl = document.getElementById('recording-timer');
    const audioPlayback = document.getElementById('audio-playback');
    const recordedAudio = document.getElementById('recorded-audio');
    const voiceDebug = document.getElementById('voice-debug');

    // Проверка поддержки MediaRecorder
    function checkMediaRecorderSupport() {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            showVoiceDebug('Браузер не поддерживает доступ к микрофону');
            return false;
        }
        
        if (!window.MediaRecorder) {
            showVoiceDebug('Браузер не поддерживает MediaRecorder API');
            return false;
        }
        
        showVoiceDebug('Микрофон поддерживается. Нажмите "Начать запись"');
        return true;
    }

    function showVoiceDebug(message) {
        voiceDebug.innerHTML = `<strong>Отладка:</strong> ${message}`;
        console.log('Voice Debug:', message);
    }

    // Переключение между методами ввода
    document.querySelectorAll('.method-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            // Деактивируем все кнопки и области
            document.querySelectorAll('.method-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.input-area').forEach(area => area.classList.remove('active'));
            
            // Активируем выбранную
            this.classList.add('active');
            const method = this.dataset.method;
            document.getElementById(`${method}-input`).classList.add('active');
            
            // Обновляем текст кнопки перевода
            const translateBtn = document.getElementById('translate-button');
            translateBtn.textContent = method === 'text' ? '🔄 Перевести' : '🎤 Обработать голос';

            // Если выбран голосовой ввод, проверяем поддержку
            if (method === 'voice') {
                checkMediaRecorderSupport();
            }
        });
    });

    // Обработка текстового перевода
    document.getElementById('translate-button').addEventListener('click', async function() {
        const activeMethod = document.querySelector('.method-btn.active').dataset.method;
        
        if (activeMethod === 'text') {
            await handleTextTranslation();
        } else {
            await handleVoiceTranslation();
        }
    });

    async function handleTextTranslation() {
        const text = document.getElementById('text-to-translate').value.trim();
        const loading = document.getElementById('loading');
        const resultArea = document.getElementById('result-area');
        const resultContent = document.getElementById('result-content');
        const translateBtn = document.getElementById('translate-button');

        if (!text) {
            showError('Пожалуйста, введите текст для перевода');
            return;
        }

        // Показываем загрузку
        loading.style.display = 'block';
        resultArea.className = 'result-area';
        translateBtn.disabled = true;

        try {
            const response = await fetch('/translate/text', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ text: text })
            });

            const data = await response.json();

            if (data.success) {
                showSuccess(`
                    <div class="original-text">
                        <strong>Исходный текст:</strong><br>
                        ${data.original_text}
                    </div>
                    <div class="translated-text">
                        <strong>Перевод:</strong><br>
                        ${data.translated_text}
                    </div>
                `);
            } else {
                showError(data.error || 'Произошла ошибка при переводе');
            }
        } catch (error) {
            showError('Ошибка соединения с сервером: ' + error.message);
        } finally {
            loading.style.display = 'none';
            translateBtn.disabled = false;
        }
    }

    async function handleVoiceTranslation() {
        if (!audioChunks.length) {
            showError('Пожалуйста, запишите голосовое сообщение');
            return;
        }

        const loading = document.getElementById('loading');
        const resultArea = document.getElementById('result-area');
        const resultContent = document.getElementById('result-content');
        const translateBtn = document.getElementById('translate-button');

        loading.style.display = 'block';
        resultArea.className = 'result-area';
        translateBtn.disabled = true;

        try {
            const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
            const formData = new FormData();
            formData.append('audio', audioBlob, 'recording.webm');

            showVoiceDebug('Отправка аудио на сервер...');

            const response = await fetch('/translate/voice', {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (data.success) {
                showSuccess(`
                    <div class="original-text">
                        <strong>Распознанная речь:</strong><br>
                        ${data.recognized_text}
                    </div>
                    <div class="translated-text">
                        <strong>Перевод:</strong><br>
                        ${data.translated_text}
                    </div>
                `);
                showVoiceDebug('Аудио успешно обработано!');
            } else {
                showError(data.error || 'Произошла ошибка при обработке голоса');
                showVoiceDebug('Ошибка: ' + data.error);
            }
        } catch (error) {
            showError('Ошибка соединения с сервером: ' + error.message);
            showVoiceDebug('Ошибка сети: ' + error.message);
        } finally {
            loading.style.display = 'none';
            translateBtn.disabled = false;
        }
    }

    function showSuccess(content) {
        const resultArea = document.getElementById('result-area');
        const resultContent = document.getElementById('result-content');
        
        resultContent.innerHTML = content;
        resultArea.className = 'result-area success';
    }

    function showError(message) {
        const resultArea = document.getElementById('result-area');
        const resultContent = document.getElementById('result-content');
        
        resultContent.innerHTML = `<p><strong>Ошибка:</strong> ${message}</p>`;
        resultArea.className = 'result-area error';
    }

    // Таймер записи
    function startTimer() {
        recordingSeconds = 0;
        recordingTimer = setInterval(() => {
            recordingSeconds++;
            const minutes = Math.floor(recordingSeconds / 60);
            const seconds = recordingSeconds % 60;
            recordingTimerEl.textContent = `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`;
        }, 1000);
    }

    function stopTimer() {
        clearInterval(recordingTimer);
        recordingSeconds = 0;
        recordingTimerEl.textContent = '00:00';
    }

    // Голосовая запись
    recordButton.addEventListener('click', async function() {
        if (!isRecording) {
            await startRecording();
        } else {
            stopRecording();
        }
    });

    async function startRecording() {
        try {
            showVoiceDebug('Запрос доступа к микрофону...');
            
            const stream = await navigator.mediaDevices.getUserMedia({ 
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    sampleRate: 44100,
                    channelCount: 1
                } 
            });
            
            showVoiceDebug('Микрофон доступен. Начинаю запись...');
            
            // Определяем поддерживаемый формат
            const options = { 
                audioBitsPerSecond: 128000,
                mimeType: 'audio/webm; codecs=opus'
            };
            
            // Пробуем разные MIME types
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                options.mimeType = 'audio/webm';
                showVoiceDebug('WebM с Opus не поддерживается, пробую WebM');
            }
            
            if (!MediaRecorder.isTypeSupported(options.mimeType)) {
                options.mimeType = 'audio/mp4';
                showVoiceDebug('WebM не поддерживается, пробую MP4');
            }
            
            mediaRecorder = new MediaRecorder(stream, options);
            audioChunks = [];

            mediaRecorder.ondataavailable = event => {
                if (event.data.size > 0) {
                    audioChunks.push(event.data);
                }
            };

            mediaRecorder.onstop = () => {
                showVoiceDebug(`Запись завершена. Размер: ${audioChunks.length} чанков`);
                
                if (audioChunks.length > 0) {
                    const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType });
                    recordedAudio.src = URL.createObjectURL(audioBlob);
                    audioPlayback.style.display = 'block';
                    showVoiceDebug('Запись готова к отправке');
                } else {
                    showVoiceDebug('Внимание: запись пустая');
                }
            };

            mediaRecorder.start(1000); // Собираем данные каждую секунду
            isRecording = true;
            
            recordButton.classList.add('recording');
            recordButton.textContent = '⏹️ Остановить запись';
            recordingStatus.style.display = 'block';
            audioPlayback.style.display = 'none';
            
            startTimer();
            showVoiceDebug('Запись началась...');
            
        } catch (error) {
            console.error('Recording error:', error);
            showVoiceDebug('Ошибка доступа к микрофону: ' + error.message);
            showError('Не удалось получить доступ к микрофону: ' + error.message);
        }
    }

    function stopRecording() {
        if (mediaRecorder && isRecording) {
            mediaRecorder.stop();
            mediaRecorder.stream.getTracks().forEach(track => track.stop());
            isRecording = false;
            
            recordButton.classList.remove('recording');
            recordButton.textContent = '🎤 Записать снова';
            recordingStatus.style.display = 'none';
            
            stopTimer();
            showVoiceDebug('Запись остановлена');
        }
    }

    // Проверяем поддержку при загрузке страницы
    document.addEventListener('DOMContentLoaded', function() {
        checkMediaRecorderSupport();
        
        // Если пользователь переходит на голосовой ввод, проверяем еще раз
        document.querySelector('.method-btn[data-method="voice"]').addEventListener('click', checkMediaRecorderSupport);
    });