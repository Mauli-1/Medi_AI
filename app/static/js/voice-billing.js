(function () {
  const SpeechRecognitionImpl = window.SpeechRecognition || window.webkitSpeechRecognition;
  const micBtn = document.getElementById('voiceMicBtn');
  const statusEl = document.getElementById('voiceStatus');
  const langSelect = document.getElementById('voiceLang');
  const confirmBar = document.getElementById('voiceConfirmBar');
  const confirmText = document.getElementById('voiceConfirmText');
  const confirmApply = document.getElementById('voiceConfirmApply');
  const confirmCancel = document.getElementById('voiceConfirmCancel');

  if (!SpeechRecognitionImpl) {
    if (micBtn) micBtn.classList.add('d-none');
    if (statusEl) statusEl.textContent = 'Voice billing not supported in this browser';
    return;
  }

  if (window.isSecureContext === false) {
    if (statusEl) statusEl.textContent = 'Voice billing requires HTTPS or localhost (not a plain IP address).';
    if (micBtn) micBtn.disabled = true;
    return;
  }

  let recognition;
  try {
    recognition = new SpeechRecognitionImpl();
  } catch (e) {
    console.error('Voice billing: failed to initialize SpeechRecognition', e);
    if (statusEl) statusEl.textContent = 'Voice billing failed to initialize: ' + e.message;
    if (micBtn) micBtn.disabled = true;
    return;
  }
  recognition.continuous = false;
  recognition.interimResults = false;
  let listening = false;
  let pendingAction = null;

  function setLang() {
    recognition.lang = langSelect ? langSelect.value : 'en-IN';
  }
  setLang();
  if (langSelect) langSelect.addEventListener('change', setLang);

  micBtn.addEventListener('click', () => {
    if (listening) { recognition.stop(); return; }
    setLang();
    try {
      recognition.start();
    } catch (e) {
      console.error('Voice billing: recognition.start() failed', e);
      statusEl.textContent = 'Could not start listening: ' + e.message;
    }
  });

  recognition.addEventListener('start', () => {
    listening = true;
    micBtn.classList.add('btn-danger');
    micBtn.classList.remove('btn-outline-secondary');
    statusEl.textContent = '🎤 Listening...';
  });

  recognition.addEventListener('end', () => {
    listening = false;
    micBtn.classList.remove('btn-danger');
    micBtn.classList.add('btn-outline-secondary');
  });

  recognition.addEventListener('error', (e) => {
    console.error('Voice billing recognition error:', e.error);
    if (e.error === 'not-allowed' || e.error === 'service-not-allowed') {
      statusEl.textContent = 'Microphone access denied. Allow microphone permission for this site in the browser address bar.';
    } else if (e.error === 'no-speech') {
      statusEl.textContent = 'No speech detected. Try again.';
    } else {
      statusEl.textContent = 'Voice error: ' + e.error;
    }
  });

  recognition.addEventListener('result', (event) => {
    const result = event.results[0][0];
    const transcript = result.transcript.trim();
    const confidence = typeof result.confidence === 'number' ? result.confidence : 1;
    statusEl.textContent = `Heard: "${transcript}"`;

    const action = parseCommand(transcript);
    if (!action) {
      statusEl.textContent = `Heard: "${transcript}" (not understood)`;
      return;
    }

    if (confidence && confidence < 0.85) {
      pendingAction = action;
      confirmText.textContent = `Heard: "${transcript}" — apply this command?`;
      confirmBar.classList.remove('d-none');
      return;
    }
    applyAction(action);
  });

  confirmApply.addEventListener('click', () => {
    if (pendingAction) applyAction(pendingAction);
    pendingAction = null;
    confirmBar.classList.add('d-none');
  });
  confirmCancel.addEventListener('click', () => {
    pendingAction = null;
    confirmBar.classList.add('d-none');
  });

  function parseCommand(text) {
    const t = text.toLowerCase();

    if (/generate (bill|invoice)|checkout/.test(t)) {
      return { type: 'checkout' };
    }

    let m = t.match(/(?:apply\s+)?(\d+)\s*(?:percent|per\s*cent|%)\s*discount/);
    if (m) return { type: 'discount', value: parseInt(m[1], 10) };

    m = t.match(/quantity\s+(\d+)/);
    if (m) return { type: 'quantity', value: parseInt(m[1], 10) };

    m = t.match(/^add\s+(.+?)(?:\s+(\d+)\s*(?:strips?|tablets?|units?))?$/);
    if (m) return { type: 'add', name: m[1].trim(), qty: m[2] ? parseInt(m[2], 10) : 1 };

    return null;
  }

  function applyAction(action) {
    if (action.type === 'checkout') {
      if (typeof generateInvoice === 'function') generateInvoice();
      return;
    }
    if (action.type === 'discount') {
      const el = document.getElementById('invoiceDisc');
      el.value = action.value;
      el.dispatchEvent(new Event('input'));
      return;
    }
    if (action.type === 'quantity') {
      if (typeof lastAddedIndex !== 'undefined' && lastAddedIndex >= 0 && typeof updateQty === 'function') {
        updateQty(lastAddedIndex, action.value);
      }
      return;
    }
    if (action.type === 'add') {
      fetch(`/sales/api/medicine-search?q=${encodeURIComponent(action.name)}`)
        .then(r => r.json())
        .then(meds => {
          if (!meds.length) { statusEl.textContent = `No medicine found for "${action.name}"`; return; }
          const med = meds[0];
          if (typeof addToCart === 'function') addToCart(med);
          if (action.qty > 1 && typeof cart !== 'undefined' && typeof updateQty === 'function') {
            updateQty(cart.length - 1, action.qty);
          }
        });
    }
  }
})();
