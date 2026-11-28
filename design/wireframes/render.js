/* Nối wireframe với dữ liệu thật sinh từ pipeline (window.NURSEFLOW_DEMO).
   Dữ liệu nạp qua <script src="demo-data.js"> nên chạy được cả khi mở bằng file://
   (không cần fetch). Không có dữ liệu → giữ nguyên mock tĩnh. */
(function () {
  "use strict";
  var D = window.NURSEFLOW_DEMO;
  if (!D) return;

  var SHIFT_LEN = D.shift.shift_length_min;
  var START_MIN = D.display_start_min;

  function pct(min) { return (min / SHIFT_LEN) * 100; }
  function clock(min) {
    var t = START_MIN + min, h = Math.floor(t / 60), m = t % 60;
    return (h < 10 ? "0" : "") + h + ":" + (m < 10 ? "0" : "") + m;
  }
  function el(html) { var d = document.createElement("div"); d.innerHTML = html.trim(); return d.firstChild; }
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) {
    return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]; }); }

  // Pack intervals vào làn (greedy) để hiện việc song song.
  function lanes(items) {
    var out = [];
    items.slice().sort(function (a, b) { return a.start - b.start; }).forEach(function (it) {
      var i = 0;
      for (; i < out.length; i++) { if (out[i][out[i].length - 1].end <= it.start) { out[i].push(it); return; } }
      out.push([it]);
    });
    return out;
  }

  function axisRow(label) {
    var hh = "";
    [0, 25, 50, 75].forEach(function (p) {
      hh += '<span class="hh" style="left:' + p + '%">' + clock(SHIFT_LEN * p / 100) + "</span>";
    });
    hh += '<span class="hh end">' + clock(SHIFT_LEN) + "</span>";
    return '<div class="r"><div class="lab">' + label + '</div><div class="area axis">' + hh + "</div></div>";
  }

  function barHTML(it) {
    var cls = it.break ? "bar break" : "bar";
    var title = (it.title || "") + " · " + clock(it.start) + "–" + clock(it.end);
    return '<div class="' + cls + '" style="left:' + pct(it.start) + "%;width:" + pct(it.end - it.start) +
      '%" title="' + esc(title) + '">' + (it.break ? "" : esc(it.label || "")) + "</div>";
  }

  function trackRow(label, items) {
    var bars = items.map(barHTML).join("");
    return '<div class="r"><div class="lab">' + esc(label) + '</div><div class="area track">' + bars + "</div></div>";
  }

  function typeOf(taskId) {
    var t = D.tasks.filter(function (x) { return x.task_id === taskId; })[0];
    return t ? t.task_type : taskId;
  }
  function patientOf(taskId) {
    var t = D.tasks.filter(function (x) { return x.task_id === taskId; })[0];
    return t ? t.patient_id : "";
  }

  function itemsForNurse(nid) {
    var items = D.plan.assignments.filter(function (a) { return a.nurse_id === nid; }).map(function (a) {
      return { start: a.start, end: a.end, label: typeOf(a.task_id),
               title: a.task_id + " · " + typeOf(a.task_id) + " · " + patientOf(a.task_id) };
    });
    D.plan.breaks.filter(function (b) { return b.nurse_id === nid; }).forEach(function (b) {
      items.push({ start: b.start, end: b.end, break: true, title: "Nghỉ được bảo vệ" });
    });
    return items;
  }

  function setOverview(cells) {
    var ov = document.getElementById("ov"); if (!ov) return;
    ov.innerHTML = cells.map(function (c) {
      return '<div class="cell"><div class="num' + (c.accent ? " accent" : "") + '">' + esc(c.num) +
        '</div><div class="lab">' + esc(c.lab) + "</div></div>";
    }).join("");
  }

  function setChat(aiText) {
    var log = document.getElementById("chatlog"); if (!log) return;
    var msg = el('<div class="msg ai"><div class="who">AI · ' + esc(D.model.name || "model") +
      '</div><div class="bub">' + esc(aiText) + "</div></div>");
    log.replaceChildren(msg);
  }

  function renderNurse() {
    var me = D.nurses[0];
    var items = itemsForNurse(me.nurse_id);
    var tasks = items.filter(function (i) { return !i.break; });
    // timeline
    var tl = document.getElementById("tl");
    if (tl) {
      var rows = axisRow("Giờ");
      lanes(items).forEach(function (lane, i) { rows += trackRow("Làn " + (i + 1), lane); });
      tl.innerHTML = rows;
    }
    // overview
    var mins = tasks.reduce(function (s, t) { return s + (t.end - t.start); }, 0);
    var pts = {};
    D.plan.assignments.filter(function (a) { return a.nurse_id === me.nurse_id; })
      .forEach(function (a) { pts[patientOf(a.task_id)] = 1; });
    var br = D.plan.breaks.filter(function (b) { return b.nurse_id === me.nurse_id; })[0];
    setOverview([
      { num: tasks.length, lab: "Việc được giao" },
      { num: mins + "'", lab: "Tổng thời lượng" },
      { num: Object.keys(pts).length, lab: "Bệnh nhân" },
      { num: br ? clock(br.start) : "—", lab: "Giờ nghỉ" }
    ]);
    // order
    var order = document.getElementById("order");
    if (order) {
      order.innerHTML = tasks.sort(function (a, b) { return a.start - b.start; }).map(function (t, i) {
        return '<div class="grp"><div class="step"><span class="idx">' + (i + 1) +
          '</span>' + esc(t.label) + '<span class="k">' + clock(t.start) + "–" + clock(t.end) + "</span></div></div>";
      }).join('<div class="arrow">↓</div>');
    }
    setChat(D.ai_text);
    // header name
    var nm = document.querySelector(".userbar .name");
    if (nm) nm.textContent = "ĐD. " + me.name;
  }

  function renderLead() {
    var tl = document.getElementById("tl");
    if (tl) {
      var rows = axisRow("Điều dưỡng");
      D.nurses.forEach(function (n) { rows += trackRow(n.name, itemsForNurse(n.nurse_id)); });
      tl.innerHTML = rows;
    }
    var m = D.plan.metrics;
    setOverview([
      { num: D.nurses.length, lab: "Điều dưỡng trực" },
      { num: D.plan.assignments.length, lab: "Tổng công việc" },
      { num: m.utilization_cv.toFixed(2), lab: "CV tải (thấp = đều)" },
      { num: D.plan.approval_required ? "Chờ duyệt" : "—", lab: "Kế hoạch", accent: true },
      { num: D.plan.validation.valid ? "Đạt" : "Cần kiểm tra", lab: "Kiểm ràng buộc" }
    ]);
    setChat(D.ai_text);
  }

  document.addEventListener("DOMContentLoaded", function () {
    try {
      var view = document.body.getAttribute("data-view");
      if (view === "lead") renderLead(); else renderNurse();
      document.querySelector(".brand .ctx").textContent =
        "Ca tổng hợp · " + clock(0) + "–" + clock(SHIFT_LEN);
      document.querySelector(".role-tag").textContent = "Bản nháp chờ trưởng ca duyệt";
      document.querySelectorAll(".composer input, .composer button").forEach(function (control) {
        control.disabled = true;
      });
      document.querySelector(".composer .hint").textContent =
        "Bản xem lịch đã xuất. Dùng CLI để gửi yêu cầu và tạo bản nháp mới.";
      if (D.model.provider === "fake") {
        document.querySelector("#chatlog .bub").textContent =
          D.plan.explanation + " Lời gọi model đang ở chế độ fake để kiểm luồng.";
      }
    } catch (e) {
      document.querySelector(".page-h").textContent = "Cần tạo lại dữ liệu demo";
      document.querySelectorAll("#tl, #ov, #order, #chatlog").forEach(function (node) {
        node.replaceChildren();
      });
      console.warn(e);
    }
  });
})();
