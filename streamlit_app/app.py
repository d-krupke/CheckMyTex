"""
CheckMyTex Streamlit App

A student-friendly web interface for analyzing LaTeX documents.
"""

from __future__ import annotations

import shutil

import streamlit as st

from components import render_file_upload, render_problem_viewer, render_todo_manager
from utils import run_analysis

# Page configuration
st.set_page_config(
    page_title="CheckMyTex - LaTeX Document Checker",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem 0;
    }
    .sub-header {
        font-size: 1.2rem;
        text-align: center;
        color: #666;
        margin-bottom: 2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Initialize session state
if "analyzed_document" not in st.session_state:
    st.session_state.analyzed_document = None
if "extract_dir" not in st.session_state:
    st.session_state.extract_dir = None


def main():
    """Main application logic."""

    # Header
    st.markdown('<div class="main-header">📝 CheckMyTex</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Student-Friendly LaTeX Document Checker</div>',
        unsafe_allow_html=True,
    )

    # Sidebar
    with st.sidebar:
        st.image(
            "https://raw.githubusercontent.com/streamlit/streamlit/develop/docs/_static/favicon.png",
            width=50,
        )
        st.title("Navigation")

        page = st.radio(
            "Go to:",
            ["📁 Upload & Analyze", "🔍 View Problems", "📋 Todo List", "ℹ️ About"],
            label_visibility="collapsed",
        )

        st.divider()

        # Statistics in sidebar if analyzed
        if st.session_state.analyzed_document:
            st.subheader("📊 Quick Stats")
            problems = st.session_state.analyzed_document.problems
            st.metric("Total Problems", len(problems))
            if "todos" in st.session_state:
                st.metric("Todo Items", len(st.session_state.todos))

        st.divider()

        # Reset button
        if st.button("🔄 Reset & Start Over", use_container_width=True):
            # Cleanup
            if st.session_state.extract_dir:
                try:
                    shutil.rmtree(st.session_state.extract_dir)
                except Exception:
                    pass

            # Clear session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]

            st.rerun()

    # Main content area
    if page == "📁 Upload & Analyze":
        render_upload_page()
    elif page == "🔍 View Problems":
        render_problems_page()
    elif page == "📋 Todo List":
        render_todo_page()
    elif page == "ℹ️ About":
        render_about_page()


def render_upload_page():
    """Render the upload and analyze page."""
    result = render_file_upload()

    if result is not None:
        extract_dir, main_tex_path = result

        st.divider()

        # Analyze button
        if st.button("🚀 Analyze Document", type="primary", use_container_width=True):
            # Progress tracking
            progress_bar = st.progress(0)
            status_text = st.empty()

            def progress_callback(message: str):
                status_text.text(message)

            try:
                # Run analysis
                progress_bar.progress(10)
                status_text.text("Starting analysis...")

                analyzed_document = run_analysis(
                    main_tex_path,
                    whitelist_path=extract_dir / ".whitelist.txt",
                    progress_callback=progress_callback,
                )

                progress_bar.progress(100)
                status_text.text("Analysis complete!")

                # Store in session state
                st.session_state.analyzed_document = analyzed_document

                st.success(f"✅ Analysis complete! Found {len(analyzed_document.problems)} problems.")
                st.info("👉 Go to 'View Problems' to review and manage them.")

            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.exception(e)
            finally:
                progress_bar.empty()
                status_text.empty()


def render_problems_page():
    """Render the problems viewing page."""
    if st.session_state.analyzed_document is None:
        st.warning("⚠️ No document has been analyzed yet. Please upload and analyze a document first.")
        return

    render_problem_viewer(st.session_state.analyzed_document)


def render_todo_page():
    """Render the todo list page."""
    render_todo_manager()


def render_about_page():
    """Render the about page."""
    st.header("ℹ️ About CheckMyTex")

    st.markdown(
        """
        CheckMyTex is a comprehensive tool for checking LaTeX documents for common errors.
        This Streamlit interface provides a student-friendly way to:

        - Upload and analyze LaTeX projects
        - Review problems with context and suggestions
        - Build a personal todo list for fixing issues
        - Export todos for offline work

        ## Features

        ### 🔍 Comprehensive Checks
        - **Spelling**: Detects typos and misspellings
        - **Grammar**: Checks grammar using LanguageTool
        - **LaTeX**: Validates LaTeX syntax with ChkTeX
        - **Style**: Suggests improvements with Proselint
        - **Formatting**: Checks for proper use of siunitx, cleveref, etc.

        ### 📋 Interactive Todo Management
        - Add problems to your personal todo list
        - Add comments and notes
        - Set priorities (high/normal/low)
        - Track status (pending/in progress/completed)
        - Export to JSON, CSV, or Markdown

        ### 🔒 Security
        - Secure file upload with validation
        - Size limits to prevent abuse
        - Whitelisted file extensions
        - Path traversal protection

        ## How to Use

        1. **Upload**: ZIP your LaTeX project and upload it
        2. **Analyze**: Click "Analyze Document" to run all checks
        3. **Review**: Browse through problems and decide what to do
        4. **Organize**: Add important issues to your todo list
        5. **Export**: Download your todo list for offline work

        ## Actions Available

        - **📋 Add to Todo**: Save the problem to work on later
        - **⏭️ Skip**: Ignore this specific problem
        - **✅ Whitelist**: Mark as false positive (won't show again)
        - **🚫 Ignore Rule**: Ignore all problems from this rule
        - **🔍 Lookup**: Search online for more information

        ## Tips

        - Start with high-priority issues
        - Add notes to remember why you added something
        - Use filters to focus on specific types of problems
        - Export regularly to track your progress

        ## Requirements

        For the best experience, your LaTeX project should:
        - Be a valid ZIP file (< 100MB)
        - Contain at least one .tex file
        - Have a clear main document (main.tex, thesis.tex, etc.)

        ## Credits

        Built with ❤️ using:
        - [CheckMyTex](https://github.com/d-krupke/checkmytex) - Core analysis engine
        - [Streamlit](https://streamlit.io/) - Web framework
        - [LanguageTool](https://languagetool.org/) - Grammar checking
        - [ChkTeX](https://www.nongnu.org/chktex/) - LaTeX validation

        ## Version

        Streamlit App v1.0.0
        """
    )


if __name__ == "__main__":
    main()
