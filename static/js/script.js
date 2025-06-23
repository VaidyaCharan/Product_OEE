function updateTime() {
  const now = new Date();
  document.getElementById('current-time').textContent =
    `${now.toLocaleDateString()} | ${now.toLocaleTimeString()}`;
}
setInterval(updateTime, 1000);
updateTime();






