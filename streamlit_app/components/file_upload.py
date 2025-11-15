"""File upload component for Streamlit."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional, Tuple

import streamlit as st

from utils.security import extract_zip_safely, find_main_tex, find_tex_files, validate_zip


def render_file_upload() -> Optional[Tuple[Path, Path]]:
    """
    Render the file upload component.

    Returns:
        Tuple of (extract_directory, main_tex_file) or None if not uploaded yet
    """
    st.header("📁 Upload Your LaTeX Project")

    st.markdown(
        """
        Upload your LaTeX project as a ZIP file. The app will analyze it for common errors
        and help you create a todo list for fixing them.

        **Tips:**
        - Maximum file size: 100 MB
        - Supported formats: .tex, .bib, .pdf, .png, .jpg, and common LaTeX files
        - The app will automatically try to find your main .tex file
        """
    )

    uploaded_file = st.file_uploader(
        "Choose a ZIP file",
        type=["zip"],
        help="Upload a ZIP archive containing your LaTeX project",
    )

    if uploaded_file is None:
        return None

    # Validate the ZIP file
    with st.spinner("Validating ZIP file..."):
        is_valid, error_msg = validate_zip(uploaded_file)

    if not is_valid:
        st.error(f"❌ {error_msg}")
        return None

    st.success("✅ ZIP file validated successfully!")

    # Extract the ZIP file
    with st.spinner("Extracting files..."):
        try:
            extract_dir, extracted_files = extract_zip_safely(uploaded_file)
            st.success(f"✅ Extracted {len(extracted_files)} files")

            # Store in session state for cleanup later
            if "extract_dir" in st.session_state and st.session_state.extract_dir != extract_dir:
                # Clean up old directory
                try:
                    shutil.rmtree(st.session_state.extract_dir)
                except Exception:
                    pass

            st.session_state.extract_dir = extract_dir

        except Exception as e:
            st.error(f"❌ Error extracting ZIP: {str(e)}")
            return None

    # Find .tex files
    tex_files = find_tex_files(extract_dir)

    if not tex_files:
        st.error("❌ No .tex files found in the ZIP archive!")
        return None

    # Try to find main .tex file
    main_tex = find_main_tex(extract_dir)

    st.subheader("📄 Select Main TeX File")

    if main_tex:
        st.info(f"🎯 Auto-detected main file: `{main_tex.name}`")

    # Let user select or confirm
    tex_file_names = [str(f.relative_to(extract_dir)) for f in tex_files]
    default_index = 0

    if main_tex:
        try:
            default_index = tex_file_names.index(str(main_tex.relative_to(extract_dir)))
        except ValueError:
            pass

    selected_file = st.selectbox(
        "Main .tex file:",
        tex_file_names,
        index=default_index,
        help="Select the main .tex file for your document",
    )

    if selected_file:
        main_tex_path = extract_dir / selected_file
        st.success(f"✅ Using: `{selected_file}`")

        # Show file preview
        with st.expander("👀 Preview first 20 lines"):
            try:
                content = main_tex_path.read_text(encoding="utf-8", errors="ignore")
                lines = content.split("\n")[:20]
                st.code("\n".join(lines), language="latex")
            except Exception as e:
                st.error(f"Could not preview file: {e}")

        return extract_dir, main_tex_path

    return None
