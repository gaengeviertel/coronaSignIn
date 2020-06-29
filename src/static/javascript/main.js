window.onload = function () {
  const storedData = JSON.parse(window.localStorage.getItem("saved-form"));
  if (storedData !== null && typeof storedData === "object") {
    if (storedData.first_name) {
      document.getElementById("first_name").value = storedData.first_name;
    }
    if (storedData.last_name) {
      document.getElementById("last_name").value = storedData.last_name;
    }
    if (storedData.contact_data) {
      document.getElementById("contact_data").value = storedData.contact_data;
    }
    // They selected save for later last time, so we assume they want to keep that
    document.getElementById("save_for_next_time").checked = true;
  }

  document
    .getElementsByTagName("form")[0]
    .addEventListener("submit", function () {
      if (document.getElementById("save_for_next_time").checked) {
        window.localStorage.setItem(
          "saved-form",
          JSON.stringify({
            first_name: document.getElementById("first_name").value,
            last_name: document.getElementById("last_name").value,
            contact_data: document.getElementById("contact_data").value,
          })
        );
      } else {
        window.localStorage.clear();
      }
    });
};
