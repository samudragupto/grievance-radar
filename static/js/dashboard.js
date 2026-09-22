// Officer dashboard decision handling: Confirm, Dismiss, Edit.

async function applyDecision(findingId, action, editedTitle = null, editedDept = null) {
  const card = document.getElementById(`card-${findingId}`);
  const payload = {
    finding_id: findingId,
    action: action,
    edited_title: editedTitle,
    edited_dept: editedDept,
  };

  try {
    const res = await fetch('/officer/decision', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    const data = await res.json();
    if (res.ok) {
      // Visual feedback and transition
      if (card) {
        card.style.opacity = '0.5';
        card.style.pointerEvents = 'none';
        setTimeout(() => {
          card.remove();
          updateCounters(action);
          checkEmptyState();
        }, 300);
      }
    } else {
      alert(data.error || 'Failed to apply decision.');
    }
  } catch (err) {
    alert('Network error while recording decision.');
  }
}

function toggleEditMode(findingId) {
  const form = document.getElementById(`edit-form-${findingId}`);
  const actions = document.getElementById(`actions-${findingId}`);
  if (!form || !actions) return;

  if (form.style.display === 'none' || form.style.display === '') {
    form.style.display = 'block';
    actions.style.display = 'none';
  } else {
    form.style.display = 'none';
    actions.style.display = 'flex';
  }
}

function saveEditAndConfirm(findingId) {
  const titleInput = document.getElementById(`edit-title-${findingId}`);
  const deptInput = document.getElementById(`edit-dept-${findingId}`);

  const editedTitle = titleInput ? titleInput.value.trim() : null;
  const editedDept = deptInput ? deptInput.value.trim() : null;

  applyDecision(findingId, 'edit', editedTitle, editedDept);
}

function updateCounters(action) {
  const pendingEl = document.getElementById('pendingCounter');
  const confirmedEl = document.getElementById('confirmedCounter');
  const dismissedEl = document.getElementById('dismissedCounter');

  if (pendingEl) {
    const cur = parseInt(pendingEl.innerText || '0');
    pendingEl.innerText = Math.max(0, cur - 1);
  }

  if (action === 'confirm' || action === 'edit') {
    if (confirmedEl) {
      const cur = parseInt(confirmedEl.innerText || '0');
      confirmedEl.innerText = cur + 1;
    }
  } else if (action === 'dismiss') {
    if (dismissedEl) {
      const cur = parseInt(dismissedEl.innerText || '0');
      dismissedEl.innerText = cur + 1;
    }
  }
}

function checkEmptyState() {
  const container = document.getElementById('findingsContainer');
  const remainingCards = container.querySelectorAll('.finding-card');
  if (remainingCards.length === 0) {
    container.innerHTML = `
      <div class="card" style="text-align: center; padding: 3rem 1.5rem;">
        <h3 style="color: var(--accent-green); margin-bottom: 0.5rem;">All Findings Processed</h3>
        <p style="color: var(--text-muted); font-size: 0.95rem;">You have reviewed all flagged anomalies for this briefing cycle.</p>
        <a href="/brief/preview" class="btn btn-primary" style="margin-top: 1rem;">View Monday Brief Preview &rarr;</a>
      </div>
    `;
  }
}
