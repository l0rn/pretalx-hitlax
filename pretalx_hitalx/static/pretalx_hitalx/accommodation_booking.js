document.addEventListener("DOMContentLoaded", function () {
  var sel = document.getElementById("id_speaker");
  if (sel && typeof Choices !== "undefined") {
    new Choices(sel, {
      searchEnabled: true,
      itemSelectText: "",
      shouldSort: false,
      allowHTML: false,
    });
  }
});
