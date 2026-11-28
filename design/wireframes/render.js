(function () {
  "use strict";

  var byId = function (id) { return document.getElementById(id); };
  var taskNames = new Map([
    ["med_admin", "Cho dùng thuốc"],
    ["vitals", "Đo dấu hiệu sinh tồn"],
    ["wound_care", "Chăm sóc vết thương"],
    ["lab_collection", "Lấy mẫu xét nghiệm"],
    ["iv_care", "Chăm sóc đường truyền"],
    ["catheter_care", "Chăm sóc ống thông"],
    ["procedure_care", "Chăm sóc liên quan thủ thuật"],
    ["hygiene", "Hỗ trợ vệ sinh"]
  ]);

  function esc(value) {
    return String(value).replace(/[&<>"]/g, function (character) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[character];
    });
  }

  async function api(path, body) {
    var response = await fetch(path, body === undefined ? {} : {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify(body)
    });
    var data = await response.json();
    if (response.status === 401) {
      location.replace("login.html");
      throw new Error("Phiên đăng nhập đã kết thúc.");
    }
    if (!response.ok) throw new Error(data.message || "Chưa kết nối được máy chủ demo.");
    return data;
  }

  function renderDraft(draft) {
    var shiftLength = draft.shift.shift_length_min;
    var lastEnd = Math.max.apply(null, draft.plan.assignments.concat(draft.plan.breaks)
      .map(function (entry) { return entry.end; }));
    var length = byId("full-shift").checked ? shiftLength :
      Math.min(shiftLength, Math.max(120, Math.ceil(lastEnd / 30) * 30));
    function clock(minute) {
      var time = draft.display_start_min + minute;
      return String(Math.floor(time / 60)).padStart(2, "0") + ":" +
        String(time % 60).padStart(2, "0");
    }
    function percent(minute) { return (minute * 100 / length) + "%"; }
    var tasks = new Map(draft.tasks.map(function (task) { return [task.task_id, task]; }));
    var step = length <= 240 ? 30 : 60;
    var axis = "";
    for (var minute = 0; minute < length; minute += step) {
      axis += '<span class="hh" style="left:' + percent(minute) + '">' + clock(minute) + '</span>';
    }
    axis += '<span class="hh end">' + clock(length) + '</span>';
    byId("tl").style.setProperty("--grid-step", percent(step));
    byId("full-shift").onchange = function () { renderDraft(draft); };
    var timeline = '<div class="r"><div class="lab">Điều dưỡng</div><div class="area axis">' + axis + '</div></div>';
    var rows = [];
    draft.nurses.forEach(function (nurse) {
      var items = draft.plan.assignments.filter(function (task) { return task.nurse_id === nurse.nurse_id; })
        .map(function (assignment) {
          var task = tasks.get(assignment.task_id);
          return {
            start: assignment.start, end: assignment.end, label: task.task_id,
            detail: task.task_id + " · " + (taskNames.get(task.task_type) || task.task_type) +
              " · " + task.patient_id
          };
        });
      draft.plan.breaks.filter(function (slot) { return slot.nurse_id === nurse.nurse_id; })
        .forEach(function (slot) {
          items.push({start: slot.start, end: slot.end, label: "Nghỉ", detail: "Nghỉ được bảo vệ", isBreak: true});
        });
      var bars = items.sort(function (a, b) { return a.start - b.start; }).map(function (item) {
        var interval = clock(item.start) + "–" + clock(item.end);
        rows.push("<tr><td>" + esc(nurse.name) + "</td><td>" + interval + "</td><td>" +
          esc(item.detail) + "</td></tr>");
        return '<div class="bar' + (item.isBreak ? ' break' : '') + '" style="left:' +
          percent(item.start) + ';width:' + percent(item.end - item.start) +
          '" title="' + esc(item.detail + " · " + interval) + '">' + esc(item.label) + '</div>';
      }).join("");
      timeline += '<div class="r"><div class="lab">' + esc(nurse.name) +
        '</div><div class="area track">' + bars + '</div></div>';
    });
    byId("tl").innerHTML = timeline;
    byId("schedule-rows").innerHTML = rows.join("");
    byId("ov").innerHTML = [
      [draft.nurses.length, "Điều dưỡng trực"],
      [draft.plan.assignments.length, "Công việc đã xếp"],
      [draft.plan.metrics.utilization_cv.toFixed(3), "CV tải"],
      ["Đạt", "Kiểm ràng buộc"]
    ].map(function (cell) {
      return '<div class="cell"><div class="num">' + esc(cell[0]) +
        '</div><div class="lab">' + esc(cell[1]) + '</div></div>';
    }).join("");
    byId("plan-status").textContent = "Bản nháp chờ trưởng ca duyệt";
    byId("draft").hidden = false;
  }

  function appendMessage(kind, name, text) {
    var log = byId("chatlog");
    var message = document.createElement("div");
    message.className = "msg " + kind;
    message.innerHTML = '<div class="who">' + esc(name) + '</div><div class="bub">' + esc(text) + '</div>';
    log.appendChild(message);
    log.scrollTop = log.scrollHeight;
    return message;
  }

  function setupChat() {
    var form = byId("chat-form");
    var input = byId("prompt");
    var button = form.querySelector("button");
    byId("example-prompt").addEventListener("click", function (event) {
      input.value = event.currentTarget.textContent.trim();
      input.focus();
    });
    form.addEventListener("submit", async function (event) {
      event.preventDefault();
      var message = input.value.trim();
      if (!message || button.disabled) return;
      byId("chat-intro")?.remove();
      appendMessage("me", "Trưởng ca", message);
      input.value = "";
      input.disabled = button.disabled = true;
      var pending = appendMessage("ai", "NurseFlow", "Đang xử lý yêu cầu…");
      try {
        var data = await api("/api/chat", {message: message});
        pending.remove();
        if (data.draft) renderDraft(data.draft);
        var usage = data.usage;
        var name = usage && usage.models.length ? "AI · " + usage.models.join(", ") + " · " +
          usage.tokens_in + "/" + usage.tokens_out + " token" : "NurseFlow";
        var reply = appendMessage("ai", name, data.message);
        var log = byId("chatlog");
        if (reply.offsetHeight > log.clientHeight) log.scrollTop = reply.offsetTop;
      } catch (error) {
        pending.remove();
        appendMessage("ai", "NurseFlow", error.message);
        input.value = message;
      } finally {
        input.disabled = button.disabled = false;
      }
    });
  }

  document.addEventListener("DOMContentLoaded", async function () {
    try {
      var session = await api("/api/session");
      var lead = session.user.role === "lead";
      if ((document.body.dataset.view === "lead") !== lead) {
        location.replace(lead ? "lead.html" : "nurse.html");
        return;
      }
      document.querySelector(".userbar .name").textContent = session.user.name;
      byId("logout").addEventListener("click", async function (event) {
        event.preventDefault();
        try {
          await api("/api/logout", {});
          location.replace("login.html");
        } catch (error) {
          alert(error.message);
        }
      });
      if (lead) setupChat();
      document.querySelector("main").hidden = false;
    } catch (error) {
      console.warn(error.message);
    }
  }, {once: true});
})();
