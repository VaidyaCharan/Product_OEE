document.addEventListener("DOMContentLoaded", function () {
  // Swiper Init
  const swiper = new Swiper(".mySwiper", {
    slidesPerView: 3,
    spaceBetween: 30,
    loop: true,
    autoplay: {
      delay: 4000,
      disableOnInteraction: false,
    },
    pagination: {
      el: ".swiper-pagination",
      clickable: true,
    },
    breakpoints: {
      320: { slidesPerView: 1, spaceBetween: 16 },
      768: { slidesPerView: 2, spaceBetween: 24 },
      1024: { slidesPerView: 3, spaceBetween: 30 },
    }
  });

  // Search filter
  const machineSearch = document.getElementById("machineSearch");
  if (machineSearch) {
    machineSearch.addEventListener("input", function () {
      const searchValue = this.value.toLowerCase();
      const cards = document.querySelectorAll(".machine-card");
      cards.forEach(card => {
        const name = card.getAttribute("data-machine-name").toLowerCase();
        card.style.display = name.includes(searchValue) ? "flex" : "none";
      });
    });
  }

  // Live OEE Update
  async function fetchMachineData() {
    try {
      const response = await fetch('/api/machine_data');
      const data = await response.json();

      data.forEach(machine => {
        const card = document.querySelector(`.machine-card[data-machine-id="${machine.id}"]`);
        if (!card) return;

        const statRows = card.querySelectorAll('.stat-row');

        const metrics = [
          { value: machine.availability, rowIndex: 0 },
          { value: machine.performance, rowIndex: 1 },
          { value: machine.quality, rowIndex: 2 },
          { value: machine.oee, rowIndex: 3 }
        ];

        metrics.forEach(metric => {
          const row = statRows[metric.rowIndex];
          const fill = row.querySelector('.fill');
          const span = row.querySelector('span');
          if (fill) fill.style.width = `${metric.value}%`;
          if (span) span.textContent = `${metric.value.toFixed(1)}%`;
        });
      });

    } catch (err) {
      console.error("Error fetching machine data:", err);
    }
  }

  fetchMachineData();
  setInterval(fetchMachineData, 500); // refresh every 15 sec
});
