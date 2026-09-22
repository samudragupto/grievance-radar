// File upload and end-to-end pipeline execution frontend logic.

document.addEventListener('DOMContentLoaded', () => {
  const uploadForm = document.getElementById('uploadForm');
  const uploadBtn = document.getElementById('uploadBtn');
  const uploadStatus = document.getElementById('uploadStatus');
  const runPipelineBtn = document.getElementById('runPipelineBtn');
  const consoleLog = document.getElementById('consoleLog');

  function logToConsole(message) {
    const timestamp = new Date().toLocaleTimeString();
    consoleLog.innerHTML += `<br/>[${timestamp}] ${message}`;
    consoleLog.scrollTop = consoleLog.scrollHeight;
  }

  if (uploadForm) {
    uploadForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fileInput = document.getElementById('fileInput');
      if (!fileInput.files.length) return;

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);

      uploadBtn.disabled = true;
      uploadBtn.innerText = 'Uploading & Anonymizing...';
      uploadStatus.style.display = 'block';
      uploadStatus.style.color = 'var(--text-muted)';
      uploadStatus.innerText = 'Streaming file, cleaning text, and redacting citizen PII...';

      logToConsole(`Beginning upload of file: ${fileInput.files[0].name}`);

      try {
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });

        const result = await response.json();
        if (response.ok) {
          uploadStatus.style.color = 'var(--accent-green)';
          uploadStatus.innerHTML = `&check; Ingested <strong>${result.imported}</strong> complaints successfully (${result.skipped} skipped).`;
          logToConsole(`Loaded & preprocessed ${result.imported} complaints (PII redacted)`);
          
          const statComplaints = document.getElementById('statComplaints');
          if (statComplaints) {
            statComplaints.innerText = parseInt(statComplaints.innerText || '0') + result.imported;
          }
        } else {
          uploadStatus.style.color = 'var(--accent-red)';
          uploadStatus.innerText = result.error || 'Upload failed.';
          logToConsole(`[ERROR] Ingestion failed: ${result.error}`);
        }
      } catch (err) {
        uploadStatus.style.color = 'var(--accent-red)';
        uploadStatus.innerText = 'Network error while uploading.';
        logToConsole(`[ERROR] Network error: ${err.message}`);
      } finally {
        uploadBtn.disabled = false;
        uploadBtn.innerText = 'Upload & Anonymize';
      }
    });
  }

  if (runPipelineBtn) {
    runPipelineBtn.addEventListener('click', async () => {
      runPipelineBtn.disabled = true;
      runPipelineBtn.innerText = 'Running Pipeline...';

      logToConsole('Initiating AI pipeline: Embedding -> Clustering -> Spike Detection');

      const startTime = performance.now();

      try {
        const res = await fetch('/api/pipeline', { method: 'POST' });
        const data = await res.json();
        const duration = ((performance.now() - startTime) / 1000).toFixed(1);

        if (res.ok) {
          logToConsole(`Generated embeddings (384-dim) and clustered into ${data.clusters_found} groups in ${duration}s`);
          logToConsole(`Statistical analysis complete: Detected ${data.spikes_detected} spikes exceeding thresholds`);
          
          if (data.top_findings && data.top_findings.length > 0) {
            data.top_findings.forEach((f, idx) => {
              logToConsole(`  &bull; Finding #${idx + 1}: ${f.title} (Z-Score: +${f.z_score}&sigma;, ${f.affected_count} complaints)`);
            });
          }

          const statClusters = document.getElementById('statClusters');
          const statPending = document.getElementById('statPending');
          if (statClusters) statClusters.innerText = data.clusters_found;
          if (statPending) statPending.innerText = data.top_findings ? data.top_findings.length : 0;

          logToConsole(`Pipeline complete! Redirecting to Officer Dashboard in 2 seconds...`);
          setTimeout(() => {
            window.location.href = '/officer/dashboard';
          }, 2000);
        } else {
          logToConsole(`[ERROR] Pipeline failed: ${data.error || 'Unknown error'}`);
          alert(data.error || 'Pipeline execution failed.');
        }
      } catch (err) {
        logToConsole(`[ERROR] Pipeline exception: ${err.message}`);
      } finally {
        runPipelineBtn.disabled = false;
        runPipelineBtn.innerText = '▶ Run Pipeline';
      }
    });
  }
});
