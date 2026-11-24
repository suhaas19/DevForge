import { marked } from "marked";
export function render(answer) {
  document.getElementById("answer").innerHTML = marked.parse(answer);
}
