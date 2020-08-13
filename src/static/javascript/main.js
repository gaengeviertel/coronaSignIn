window.onload = function () {
  function maybeUpdateValueFromObject(obj, elementId) {
    const value = obj[elementId];
    if (value) {
      document.getElementById(elementId).value = value;
    }
  }

  const storedData = JSON.parse(window.localStorage.getItem("saved-form"));

  const form_fields = [
    "first_name",
    "last_name",
    "street_and_house_number",
    "plz_and_city",
    "phone_number",
  ];

  if (storedData !== null && typeof storedData === "object") {
    form_fields.forEach(function (field) {
      maybeUpdateValueFromObject(storedData, field);
    });

    // They selected save for later last time, so we assume they want to keep that
    document.getElementById("save_for_next_time").checked = true;
  }

  function formValuesAsJSON() {
    const data = {};
    form_fields.forEach(function (field) {
      data[field] = document.getElementById(field).value;
    });
    return JSON.stringify(data);
  }

  document
    .getElementsByTagName("form")[0]
    .addEventListener("submit", function () {
      if (document.getElementById("save_for_next_time").checked) {
        window.localStorage.setItem("saved-form", formValuesAsJSON());
      } else {
        window.localStorage.clear();
      }
    });
};
