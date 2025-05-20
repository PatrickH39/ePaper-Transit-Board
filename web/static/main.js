  let allData = [];
  let showAlternate = false;
  let countdown = 30; // countdown starts at 30

  async function fetchDataFromAPI() {
      try {
          const response = await fetch("/data");
          const data = await response.json();

          // Handle API error from backend
          if (data.error) {
              console.error("API error:", data.error);
              document.getElementById("bus-table-body").innerHTML = `
          <tr><td colspan="5">Error: ${data.error}</td></tr>
        `;
              return;
          }

          // Handle empty departures
          if (!data.departures || data.departures.length === 0) {
              console.warn("No departures received.");
              document.getElementById("bus-table-body").innerHTML = `
          <tr><td colspan="5">No departures available.</td></tr>
        `;
              return;
          }

          // Store data and update last-updated timestamp
          allData = data.departures;
          document.getElementById("last-updated").textContent = data.last_updated;

          // Now safe to update the table
          updateTable();

      } catch (err) {
          console.error("Fetch failed:", err);
          document.getElementById("bus-table-body").innerHTML = `
        <tr><td colspan="5">Failed to fetch data from server.</td></tr>
      `;
      }
  }



  function updateTable() {
      const tbody = document.getElementById("bus-table-body");
      tbody.innerHTML = "";

      const filtered = allData.filter(entry => {
          const dir = entry.stop;

          // eastbound / northbound on first view
          if (!showAlternate) {
              return dir.includes("Eastbound") || dir.includes("Northbound");
          }

          // westbound / southbound on second view
          return dir.includes("Westbound") || dir.includes("Southbound");
      });


      filtered.forEach(entry => {
          const row = document.createElement("tr");

          const isCancelled = entry.times.some(t => t.cancelled);
          if (isCancelled) row.classList.add("cancelled");

          let html = `
        <td class="route">${entry.route}</td>
        <td class="direction">${entry.direction}</td>
      `;

          entry.times.forEach(t => {
              // Format time (remove seconds)
              let timeDisplay = t.time;

              if (t.real_time) {
                  timeDisplay = `<span class="realtime">${timeDisplay}<img class="rt-icon" src="static/realtime.svg"></span>`;
              }

              if (t.cancelled) {
                  timeDisplay = `<span class="cancelled-text">${timeDisplay}</span>`;
              }

              html += `<td class="time">${timeDisplay}</td>`;
          });

          row.innerHTML = html;
          tbody.appendChild(row);
      });
  }

  // INITIAL DATA FETCH
  fetchDataFromAPI();

  // Update API data every 30 seconds
  setInterval(fetchDataFromAPI, 30000);

  // Toggle direction view every 30 seconds
  setInterval(() => {
      showAlternate = !showAlternate;
      countdown = 30; // reset countdown
      updateTable();
  }, 30000);