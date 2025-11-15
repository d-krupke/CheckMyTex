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
    initial_sidebar_state="auto",
)

# Custom CSS for better styling
st.markdown(
    """
    <style>
    /* Main styling */
    .main {
        padding-top: 2rem;
    }

    /* Problem card styling */
    .problem-card {
        background-color: #f8f9fa;
        border-left: 4px solid #e74c3c;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 4px;
    }

    .problem-card.warning {
        border-left-color: #f39c12;
    }

    .problem-card.info {
        border-left-color: #3498db;
    }

    /* Code blocks */
    .stCodeBlock {
        background-color: #f5f5f5;
    }

    /* Metrics */
    div[data-testid="metric-container"] {
        background-color: #f8f9fa;
        border: 1px solid #e0e0e0;
        padding: 0.5rem;
        border-radius: 0.5rem;
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
    st.title("📝 CheckMyTex")
    st.caption("Student-Friendly LaTeX Document Checker")

    # Sidebar - only show filters and stats
    with st.sidebar:
        st.header("⚙️ Settings")

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

        # Statistics if analyzed
        if st.session_state.analyzed_document:
            st.divider()
            st.header("📊 Statistics")
            problems = st.session_state.analyzed_document.problems
            st.metric("Total Problems", len(problems))
            if "todos" in st.session_state:
                st.metric("Todo Items", len(st.session_state.todos))
            if "skipped_problems" in st.session_state:
                st.metric("Skipped", len(st.session_state.skipped_problems))
            if "whitelisted_problems" in st.session_state:
                st.metric("Whitelisted", len(st.session_state.whitelisted_problems))

    # Main content with tabs
    if st.session_state.analyzed_document is None:
        # Show upload page only
        render_upload_page()
    else:
        # Show tabs for navigation
        tab1, tab2, tab3 = st.tabs(["🔍 Problems", "📋 Todo List", "ℹ️ About"])

        with tab1:
            render_problem_viewer(st.session_state.analyzed_document)

        with tab2:
            render_todo_manager()

        with tab3:
            render_about_page()


def render_upload_page():
    """Render the upload and analyze page."""
    st.header("📁 Upload & Analyze")

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
                st.info("👉 Switch to the 'Problems' tab to review them.")

                # Force rerun to show tabs
                st.rerun()

            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.exception(e)
            finally:
                progress_bar.empty()
                status_text.empty()


def render_about_page():
    """Render the about page."""
    st.markdown(
        """
        ## About CheckMyTex

        CheckMyTex is a comprehensive tool for checking LaTeX documents for common errors.

        ### 🎯 What it checks

        - **Spelling** - Detects typos and misspellings
        - **Grammar** - Checks grammar using LanguageTool
        - **LaTeX** - Validates LaTeX syntax with ChkTeX
        - **Style** - Suggests improvements with Proselint
        - **Formatting** - Checks proper use of siunitx, cleveref, etc.

        ### 🚀 How to use

        1. Upload your LaTeX project as a ZIP file
        2. Click "Analyze Document"
        3. Review problems in the Problems tab
        4. Add important items to your Todo List
        5. Export your todo list for offline work

        ### 💡 Tips

        - Add comments to remember why something needs fixing
        - Set priorities to focus on what matters most
        - Use the Skip and Whitelist actions to clean up the view
        - Export your todo list regularly to track progress

        ### 🔗 More Info

        - [CheckMyTex GitHub](https://github.com/d-krupke/checkmytex)
        - [Documentation](https://github.com/d-krupke/checkmytex#readme)
        """
    )


if __name__ == "__main__":
    main()
