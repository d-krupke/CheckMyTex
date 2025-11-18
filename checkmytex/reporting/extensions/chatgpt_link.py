"""ChatGPT help link extension for problems."""

from __future__ import annotations

import html
import urllib.parse

from ..extension_base import ExtensionContext, ProblemExtension


class ChatGptLinkExtension(ProblemExtension):
    """
    Add 'Ask ChatGPT' help links to problems.

    Conditionally renders based on:
    - Whether location info is available
    - Whether context size fits in a URL (browser limits ~2000 chars)
    """

    CHATGPT_BASE_URL = "https://chatgpt.com/"
    MAX_URL_LENGTH = 2000  # Conservative browser limit
    LINK_SNIPPET_CHAR_LIMIT = 600

    def __init__(
        self,
        model: str = "gpt-4o",
        context_lines_before: int = 3,
        context_lines_after: int = 3,
    ):
        """
        Args:
            model: ChatGPT model to request (e.g., "gpt-4o", "o1")
            context_lines_before: Code lines to show before problem
            context_lines_after: Code lines to show after problem
        """
        self.model = model
        self.context_before = context_lines_before
        self.context_after = context_lines_after

    def render_line(self, context: ExtensionContext) -> str | None:
        """Render ChatGPT link and copy button."""
        copy_prompt = self._build_prompt(context)
        link_url, link_disabled = self._prepare_link_url(context, copy_prompt)

        escaped_prompt = html.escape(copy_prompt)
        link_html = self._render_link_button(link_url, link_disabled)
        learn_more_html = self._render_learn_more_button(context.problem.look_up_url)

        return (
            f'<div class="llm-help-buttons">'
            f"{link_html}"
            f'<button class="copy-prompt-btn" data-prompt="{escaped_prompt}" '
            f'onclick="copyPromptToClipboard(this)" title="Copy prompt for any LLM">'
            f'<svg class="icon-copy" viewBox="0 0 24 24">'
            f'<path d="M19,21H8V7H19M19,5H8A2,2 0 0,0 6,7V21A2,2 0 0,0 8,23H19A2,2 0 0,0 21,21V7A2,2 0 0,0 19,5M16,1H4A2,2 0 0,0 2,3V17H4V3H16V1Z"/>'
            f"</svg>"
            f'<span class="copy-prompt-text">Copy prompt</span>'
            f"</button>"
            f"{learn_more_html}"
            f"</div>"
        )

    def priority(self) -> int:
        """Render after basic message."""
        return 100

    def get_css(self) -> str:
        return """
        .llm-help-buttons {
            display: inline-flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .chatgpt-link {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: linear-gradient(135deg, #10a37f 0%, #0d8a6a 100%);
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            transition: transform 0.2s, box-shadow 0.2s;
            cursor: pointer;
        }
        .chatgpt-link:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px rgba(16, 163, 127, 0.3);
        }
        .chatgpt-link.disabled {
            background: #4a5568;
            opacity: 0.6;
            pointer-events: none;
            cursor: not-allowed;
        }
        .icon-chatgpt {
            width: 14px;
            height: 14px;
            fill: white;
        }
        .copy-prompt-btn {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: #4a5568;
            color: white;
            border: none;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
        }
        .copy-prompt-btn:hover {
            background: #2d3748;
            transform: translateY(-1px);
        }
        .copy-prompt-btn.copied {
            background: #38a169;
        }
        .icon-copy {
            width: 14px;
            height: 14px;
            fill: white;
        }
        .lookup-link {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 6px 12px;
            background: #4a5568;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            transition: all 0.2s;
        }
        .lookup-link:hover {
            background: #2d3748;
            transform: translateY(-1px);
        }
        .icon-external {
            width: 14px;
            height: 14px;
            fill: white;
        }
        """

    def get_js(self) -> str:
        return """
        (function() {
            function fallbackCopy(text) {
                return new Promise(function(resolve, reject) {
                    const textarea = document.createElement('textarea');
                    textarea.value = text;
                    textarea.setAttribute('readonly', '');
                    textarea.style.position = 'fixed';
                    textarea.style.top = '-1000px';
                    textarea.style.opacity = '0';
                    document.body.appendChild(textarea);
                    textarea.select();
                    try {
                        const ok = document.execCommand('copy');
                        if (ok) {
                            resolve();
                        } else {
                            reject(new Error('Copy failed'));
                        }
                    } catch (err) {
                        reject(err);
                    } finally {
                        document.body.removeChild(textarea);
                    }
                });
            }

            function showCopied(button) {
                const textEl = button.querySelector('.copy-prompt-text');
                if (!textEl) {
                    return;
                }
                if (!textEl.dataset.originalText) {
                    textEl.dataset.originalText = textEl.textContent || '';
                }
                textEl.textContent = 'Copied!';
                button.classList.add('copied');
                setTimeout(function() {
                    textEl.textContent = textEl.dataset.originalText;
                    button.classList.remove('copied');
                }, 1500);
            }

            function getFallbackMessage(button) {
                const box = button.closest('.problem-box');
                if (!box) {
                    return '';
                }
                const messageEl = box.querySelector('.problem-message');
                return messageEl ? (messageEl.textContent || '') : '';
            }

            window.copyPromptToClipboard = function(button) {
                if (!button) {
                    return;
                }

                const prompt = button.dataset ? button.dataset.prompt || '' : '';
                const text = prompt || getFallbackMessage(button);
                if (!text) {
                    return;
                }

                const canUseClipboard = navigator.clipboard && navigator.clipboard.writeText;
                const copyPromise = canUseClipboard
                    ? navigator.clipboard.writeText(text).catch(function() {
                          return fallbackCopy(text);
                      })
                    : fallbackCopy(text);

                copyPromise.then(function() {
                    showCopied(button);
                });
            };
        })();
        """

    def _build_prompt(
        self,
        context: ExtensionContext,
        code_snippet: str | None = None,
        snippet_note: str | None = None,
    ) -> str:
        """Build the ChatGPT prompt."""
        problem = context.problem

        parts = [
            "I'm working on a LaTeX document and encountered this issue:\n",
            f"**Tool**: {problem.tool}",
            f"**Rule**: {problem.rule}",
            f"**Message**: {problem.message}",
        ]

        if context.has_location:
            parts.append(f"**Location**: {context.filename}:{context.line_number}")

        snippet = code_snippet if code_snippet is not None else context.code_snippet
        if snippet:
            label = "**Code Context**"
            if snippet_note:
                label += f" ({snippet_note})"
            parts.append(f"\n{label}:\n```latex\n{snippet}\n```")

        parts.extend(
            [
                "\nPlease:",
                "1. Explain what this issue means in simple terms",
                "2. Explain why it matters for my document",
                "3. Show how to fix it with a corrected code example",
                "4. Consider that this might be a false positive; if so, explain why and what to verify",
            ]
        )

        return "\n".join(parts)

    def _create_url(self, prompt: str) -> str:
        """Create ChatGPT deep link."""
        encoded = urllib.parse.quote(prompt, safe="")
        params = {"q": encoded}
        if self.model:
            params["model"] = self.model
        query = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{self.CHATGPT_BASE_URL}?{query}"

    def _prepare_link_url(
        self, context: ExtensionContext, full_prompt: str
    ) -> tuple[str, bool]:
        """Return usable link URL or flag it as disabled when too long."""
        url = self._create_url(full_prompt)
        if len(url) <= self.MAX_URL_LENGTH:
            return url, False

        reduced_snippet = self._reduce_snippet(context)
        if reduced_snippet:
            trimmed_prompt = self._build_prompt(
                context, code_snippet=reduced_snippet, snippet_note="trimmed for link"
            )
            url = self._create_url(trimmed_prompt)
            if len(url) <= self.MAX_URL_LENGTH:
                return url, False

        return "", True

    def _reduce_snippet(self, context: ExtensionContext) -> str | None:
        """Return a shorter snippet focused on the problem line."""
        snippet = context.code_snippet
        if not snippet:
            return None

        if len(snippet) <= self.LINK_SNIPPET_CHAR_LIMIT:
            return snippet

        lines = snippet.splitlines()
        if not lines:
            return None

        focus_idx = None
        if context.line_number is not None:
            target = f"{context.line_number}:"
            for idx, line in enumerate(lines):
                stripped = line.lstrip()
                if stripped.startswith(target):
                    focus_idx = idx
                    break

        if focus_idx is None:
            focus_idx = len(lines) // 2

        start = end = focus_idx
        current_len = len(lines[focus_idx])

        def line_len(i: int) -> int:
            # +1 accounts for the newline that will be reintroduced when joining
            return len(lines[i]) + 1

        while True:
            added = False
            if start > 0:
                addition = line_len(start - 1)
                if current_len + addition <= self.LINK_SNIPPET_CHAR_LIMIT:
                    start -= 1
                    current_len += addition
                    added = True
            if end < len(lines) - 1:
                addition = line_len(end + 1)
                if current_len + addition <= self.LINK_SNIPPET_CHAR_LIMIT:
                    end += 1
                    current_len += addition
                    added = True
            if not added:
                break

        snippet_lines = lines[start : end + 1]
        if start > 0:
            snippet_lines.insert(0, "... (trimmed)")
        if end < len(lines) - 1:
            snippet_lines.append("... (trimmed)")

        reduced = "\n".join(snippet_lines)
        return reduced if reduced else None

    def _render_link_button(self, url: str, disabled: bool) -> str:
        """Render the ChatGPT link or a disabled placeholder."""
        content = (
            '<svg class="icon-chatgpt" viewBox="0 0 24 24">'
            '<path d="M22.2819 9.8211a5.9847 5.9847 0 0 0-.5157-4.9108 6.0462 6.0462 0 0 0-6.5098-2.9A6.0651 6.0651 0 0 0 4.9807 4.1818a5.9847 5.9847 0 0 0-3.9977 2.9 6.0462 6.0462 0 0 0 .7427 7.0966 5.98 5.98 0 0 0 .511 4.9107 6.051 6.051 0 0 0 6.5146 2.9001A5.9847 5.9847 0 0 0 13.2599 24a6.0557 6.0557 0 0 0 5.7718-4.2058 5.9894 5.9894 0 0 0 3.9977-2.9001 6.0557 6.0557 0 0 0-.7475-7.0729zm-9.022 12.6081a4.4755 4.4755 0 0 1-2.8764-1.0408l.1419-.0804 4.7783-2.7582a.7948.7948 0 0 0 .3927-.6813v-6.7369l2.02 1.1686a.071.071 0 0 1 .038.052v5.5826a4.504 4.504 0 0 1-4.4945 4.4944zm-9.6607-4.1254a4.4708 4.4708 0 0 1-.5346-3.0137l.142.0852 4.783 2.7582a.7712.7712 0 0 0 .7806 0l5.8428-3.3685v2.3324a.0804.0804 0 0 1-.0332.0615L9.74 19.9502a4.4992 4.4992 0 0 1-6.1408-1.6464zM2.3408 7.8956a4.485 4.485 0 0 1 2.3655-1.9728V11.6a.7664.7664 0 0 0 .3879.6765l5.8144 3.3543-2.0201 1.1685a.0757.0757 0 0 1-.071 0l-4.8303-2.7865A4.504 4.504 0 0 1 2.3408 7.872zm16.5963 3.8558L13.1038 8.364 15.1192 7.2a.0757.0757 0 0 1 .071 0l4.8303 2.7913a4.4944 4.4944 0 0 1-.6765 8.1042v-5.6772a.79.79 0 0 0-.407-.667zm2.0107-3.0231l-.142-.0852-4.7735-2.7818a.7759.7759 0 0 0-.7854 0L9.409 9.2297V6.8974a.0662.0662 0 0 1 .0284-.0615l4.8303-2.7866a4.4992 4.4992 0 0 1 6.6802 4.66zM8.3065 12.863l-2.02-1.1638a.0804.0804 0 0 1-.038-.0567V6.0742a4.4992 4.4992 0 0 1 7.3757-3.4537l-.142.0805L8.704 5.459a.7948.7948 0 0 0-.3927.6813zm1.0976-2.3654l2.602-1.4998 2.6069 1.4998v2.9994l-2.5974 1.4997-2.6067-1.4997Z"/>'
            "</svg>"
            "Ask ChatGPT"
        )

        if disabled:
            return (
                '<span class="chatgpt-link disabled" title="Prompt too large for direct link" '
                'aria-disabled="true">'
                f"{content}"
                "</span>"
            )

        escaped_url = html.escape(url)
        return (
            f'<a href="{escaped_url}" class="chatgpt-link" '
            f'target="_blank" rel="noopener noreferrer">'
            f"{content}"
            "</a>"
        )

    def _render_learn_more_button(self, url: str | None) -> str:
        """Render documentation link if available."""
        if not url:
            return ""

        escaped_url = html.escape(url)
        return (
            f'<a href="{escaped_url}" class="lookup-link" '
            f'target="_blank" rel="noopener noreferrer">'
            f'<svg class="icon-external" viewBox="0 0 24 24">'
            f'<path d="M14 3v2h3.59l-9.83 9.83 1.41 1.41L19 6.41V10h2V3m-2 16H5V5h7V3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7h-2v7z"/>'
            f"</svg>"
            f"Learn more"
            f"</a>"
        )
