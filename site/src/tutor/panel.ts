import type { TutorReply } from "./types";

export function renderTurn(list: HTMLOListElement, turn: TutorReply): HTMLLIElement {
  const item = document.createElement("li");
  const reply = document.createElement("p");
  reply.className = "reply";
  reply.textContent = turn.reply;
  item.appendChild(reply);

  const hint = document.createElement("span");
  hint.className = "hint";
  hint.textContent = `Hint ${turn.hint_level} of 4`;
  item.appendChild(hint);

  const verified = turn.guard?.passed === true && (turn.numbers_cited?.length ?? 0) > 0;
  if (verified) {
    const badge = document.createElement("span");
    badge.className = "badge";
    badge.dataset.testid = "numbers-verified";
    badge.textContent = "numbers verified ✓";
    item.appendChild(badge);
  }

  for (const call of turn.tool_calls ?? []) {
    const chip = document.createElement("span");
    chip.className = "chip";
    chip.textContent = `${call.name} · ${call.source ?? "state"}`;
    item.appendChild(chip);
  }

  if (turn.source === "scripted" || turn.source === "canned") {
    const offline = document.createElement("span");
    offline.className = "offline";
    offline.textContent = "offline";
    item.appendChild(offline);
  }

  list.appendChild(item);
  return item;
}
