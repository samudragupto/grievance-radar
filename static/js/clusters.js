// Semantic cluster card dynamic updates.

document.addEventListener('DOMContentLoaded', async () => {
  try {
    const res = await fetch('/api/clusters');
    const clusters = await res.json();
    console.log(`Loaded ${clusters.length} clusters for inspection.`);
  } catch (err) {
    console.error('Failed to query cluster API:', err);
  }
});
