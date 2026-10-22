/*
 * Логика демоэкзамена (интегрированный html-стенд).
 *
 * !!! ЗАМЕНИТЕ массив QUESTIONS на задания из вашего готового html-файла,
 * либо вставьте содержимое вашего файла в demo_exam.html — при сохранении
 * вызова finishExam() результат всё равно уйдёт в базу платформы.
 */

const PASS_PERCENT = 70; // порог зачёта (задаёт преподаватель)

const QUESTIONS = [
  {
    q: "Что такое переменная?",
    options: ["Именованная ячейка памяти для хранения данных",
              "Команда запуска программы",
              "Тип файла на диске"],
    correct: 0,
    points: 1,
  },
  {
    q: "Какой метод добавляет элемент в конец списка Python?",
    options: [".push()", ".append()", ".add()"],
    correct: 1,
    points: 1,
  },
  {
    q: "Что делает оператор `==`?",
    options: ["Присваивает значение", "Сравнивает значения", "Объявляет функцию"],
    correct: 1,
    points: 1,
  },
  {
    q: "Из чего состоит адрес страницы в браузере?",
    options: ["Протокол, домен, путь", "Порт и MAC-адрес", "Только имя файла"],
    correct: 0,
    points: 1,
  },
  {
    q: "Какую базу данных использует данная платформа по умолчанию?",
    options: ["Oracle", "MongoDB", "SQLite"],
    correct: 2,
    points: 1,
  },
];

(function renderExam() {
  const form = document.getElementById("exam-form");
  QUESTIONS.forEach((item, qi) => {
    const block = document.createElement("fieldset");
    block.className = "question";
    const legend = document.createElement("legend");
    legend.textContent = `${qi + 1}. ${item.q} (${item.points} б.)`;
    block.appendChild(legend);
    item.options.forEach((opt, oi) => {
      const label = document.createElement("label");
      label.className = "option";
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = `q${qi}`;
      radio.value = oi;
      label.appendChild(radio);
      label.appendChild(document.createTextNode(" " + opt));
      block.appendChild(label);
    });
    form.appendChild(block);
  });
})();

function finishExam() {
  let score = 0;
  let maxScore = 0;
  const details = {};
  QUESTIONS.forEach((item, qi) => {
    maxScore += item.points;
    const sel = document.querySelector(`input[name="q${qi}"]:checked`);
    const answered = sel ? Number(sel.value) : -1;
    const isCorrect = answered === item.correct;
    if (isCorrect) score += item.points;
    details[`question_${qi + 1}`] = {
      answer: answered, correct: item.correct, ok: isCorrect,
    };
  });
  const percent = maxScore ? Math.round((score / maxScore) * 100) : 0;
  const passed = percent >= PASS_PERCENT;

  const summary = document.getElementById("exam-summary");
  summary.classList.remove("hidden", "ok", "fail");
  summary.classList.add(passed ? "ok" : "fail");
  summary.innerHTML =
    `Ваш результат: <b>${score} из ${maxScore}</b> (${percent}%) — ` +
    (passed ? "зачтено ✅" : "не зачтено ❌");

  // отправка результата в платформу
  fetch("/api/exam-result", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ score, max_score: maxScore, passed, details }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.ok) {
        summary.innerHTML += '<br><span class="muted">Результат сохранён в системе.</span>';
      } else {
        summary.innerHTML += '<br><span class="fail">Не удалось сохранить результат.</span>';
      }
    })
    .catch(() => {
      summary.innerHTML += '<br><span class="fail">Ошибка сети: результат не сохранён.</span>';
    });

  document.getElementById("finish-btn").disabled = true;
}

// глобальная точка входа — чтобы ваш html мог вызвать её из своего кода
window.finishExam = finishExam;
document.getElementById("finish-btn").addEventListener("click", finishExam);
