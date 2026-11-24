(function () {
  const startBtn = document.getElementById("voice-start");
  const micBtn = document.getElementById("voice-mic");
  const stopBtn = document.getElementById("voice-stop");
  const statusEl = document.getElementById("voice-status");
  const logEl = document.getElementById("chat-log");
  const scenarioEl = document.getElementById("voice-scenario");
  const form = document.getElementById("call-form");
  const resultEl = document.getElementById("call-result");

  let socket = null;
  let recognition = null;
  let listening = false;

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

  function addLine(who, text) {
    const line = document.createElement("div");
    line.className = "chat-line " + (who === "client" ? "client" : "ai");
    line.innerHTML = "<strong>" + (who === "client" ? "Вы" : "ИИ") + ":</strong> " + text;
    logEl.appendChild(line);
    logEl.scrollTop = logEl.scrollHeight;
  }

  function speak(text) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = "ru-RU";
    utterance.rate = 1;
    const voices = window.speechSynthesis.getVoices();
    const russian = voices.find((v) => v.lang && v.lang.toLowerCase().startsWith("ru"));
    if (russian) utterance.voice = russian;
    window.speechSynthesis.speak(utterance);
  }

  function setListening(on) {
    listening = on;
    micBtn.textContent = on ? "⏹ Слушаю… нажмите, чтобы остановить" : "🎤 Говорить";
  }

  function startRecognition() {
    if (!SpeechRecognition) {
      addLine("ai", "Ваш браузер не поддерживает распознавание речи. Напишите текст вручную.");
      const text = prompt("Напишите вашу реплику:");
      if (text && socket && socket.readyState === WebSocket.OPEN) {
        addLine("client", text);
        socket.send(JSON.stringify({ type: "text", text: text }));
      }
      return;
    }
    recognition = new SpeechRecognition();
    recognition.lang = "ru-RU";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;
    recognition.onstart = () => setListening(true);
    recognition.onend = () => setListening(false);
    recognition.onerror = (event) => {
      setListening(false);
      if (event.error !== "no-speech") statusEl.textContent = "Ошибка микрофона: " + event.error;
    };
    recognition.onresult = (event) => {
      const text = event.results[0][0].transcript.trim();
      if (!text) return;
      addLine("client", text);
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: "text", text: text }));
      }
    };
    recognition.start();
  }

  function stopAll() {
    if (recognition) {
      try { recognition.stop(); } catch (e) { /* уже остановлен */ }
    }
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: "stop" }));
      socket.close();
    }
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    startBtn.disabled = false;
    micBtn.disabled = true;
    stopBtn.disabled = true;
    statusEl.textContent = "Разговор завершён.";
  }

  startBtn.addEventListener("click", function () {
    const scenario = scenarioEl.value;
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    socket = new WebSocket(protocol + "//" + location.host + "/ws/browser?scenario=" + encodeURIComponent(scenario));

    socket.onopen = () => {
      statusEl.textContent = "Подключение к ИИ…";
    };
    socket.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === "ready") {
        statusEl.textContent = "ИИ на связи. Нажмите «Говорить».";
        startBtn.disabled = true;
        micBtn.disabled = false;
        stopBtn.disabled = false;
      } else if (data.type === "reply") {
        addLine("ai", data.text);
        speak(data.text);
        if (data.end) {
          statusEl.textContent = "Сценарий завершён.";
          setTimeout(stopAll, 2500);
        }
      }
    };
    socket.onerror = () => {
      statusEl.textContent = "Не удалось подключиться к серверу.";
      startBtn.disabled = false;
    };
    socket.onclose = () => {
      if (!listening) statusEl.textContent = "Соединение закрыто.";
    };
  });

  micBtn.addEventListener("click", function () {
    if (listening) {
      if (recognition) recognition.stop();
    } else {
      startRecognition();
    }
  });

  stopBtn.addEventListener("click", stopAll);

  form.addEventListener("submit", async function (event) {
    event.preventDefault();
    const payload = {
      phone: form.phone.value,
      scenario: form.scenario.value,
      provider: form.provider.value,
    };
    resultEl.textContent = "Отправляем запрос…";
    try {
      const response = await fetch("/api/calls", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await response.json();
      if (data.ok) {
        resultEl.textContent = "Звонок создан (ID " + data.call_id + "). Обновляем журнал…";
        setTimeout(() => location.reload(), 1200);
      } else {
        resultEl.textContent = "Ошибка: " + (data.detail || "неизвестная");
      }
    } catch (error) {
      resultEl.textContent = "Ошибка сети: " + error.message;
    }
  });
})();
