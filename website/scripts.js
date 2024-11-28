document.addEventListener("DOMContentLoaded", () => {
  // Define live feeds
  const liveFeeds = [
      {
          img: document.getElementById("liveFeedA"),
          timestamp: document.getElementById("timestampA"),
          file: "rpiA.jpg"
      },
      {
          img: document.getElementById("liveFeedB"),
          timestamp: document.getElementById("timestampB"),
          file: "rpiB.jpg"
      },
      {
          img: document.getElementById("liveFeedC"),
          timestamp: document.getElementById("timestampC"),
          file: "rpiC.jpg"
      }
  ];

  async function fetchAndUpdate(feed) {
      try {
          const response = await fetch(`file_info.php?file=${feed.file}&nocache=${Date.now()}`);
          if (response.ok) {
              const data = await response.json();
              if (data.lastModified) {
                  const lastModifiedTime = new Date(data.lastModified);
                  feed.img.src = `${feed.file}?timestamp=${Date.now()}`;
                  feed.timestamp.textContent = lastModifiedTime.toLocaleString();
              } else {
                  feed.timestamp.textContent = "No metadata available";
              }
          } else {
              console.error(`Error fetching metadata for ${feed.file}`);
              feed.timestamp.textContent = "Error fetching metadata";
          }
      } catch (error) {
          console.error(`Failed to fetch metadata for ${feed.file}:`, error);
          feed.timestamp.textContent = "Error fetching metadata";
      }
  }

  function refreshAllFeeds() {
      liveFeeds.forEach(feed => fetchAndUpdate(feed));
  }

  // Refresh live feeds every 5 seconds
  setInterval(refreshAllFeeds, 5000);
});