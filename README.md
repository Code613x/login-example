# Shredder – Secure File Deletion Desktop Application

**Shredder** is a Windows desktop application written in C# (.NET Framework) that allows users to **permanently delete files** from their computer. Unlike standard deletion, which only removes the file reference from the filesystem, Shredder **overwrites the file multiple times** using various algorithms, making it virtually impossible to recover the file using standard recovery tools.

This project demonstrates practical skills in **C# development, Windows Forms, file handling, and secure deletion algorithms**, and is an example of building a full-featured desktop application with a polished user interface.

---

## 🔹 Key Features

- **Drag-and-Drop Support:** Easily drop a file into the application to prepare it for deletion.
- **Browse Files:** Open a file dialog to select any file from your system.
- **Shredding Levels:** Select from 5 levels of security for overwriting:
  - **Level 1–4:** Predefined combinations of secure deletion methods
  - **Level 0:** Custom mode where the user can select individual overwrite algorithms
- **Multiple Overwrite Options:** Customize which algorithms to use for shredding, including multi-pass random data and attribute clearing.
- **Randomized Action Button Text:** Adds a fun and engaging element to the user experience.
- **Persistent User Settings:** The app saves your preferences and restores them on the next launch.
- **Validation & Feedback:** Only allows shredding if a valid file is selected and shows a confirmation message when the operation is complete.

---

## 🔹 How It Works

1. **Selecting a File**
   - Either click the **"Browse"** button to open a file dialog, or drag and drop a file into the application window.
   - The application validates the file exists before enabling the "Shred" button.

2. **Choosing a Shredding Level**
   - Use the trackbar to select a shredding level (1–5).  
   - Level 0 enables custom mode, letting you choose which overwrite methods to apply.  
   - Higher levels combine multiple secure deletion algorithms for maximum security.

3. **Customizing Overwrite Methods**
   - Checkboxes correspond to different deletion techniques:
     - Multi-pass random data
     - Attribute clearing
     - Directory and metadata shredding
   - Available only in custom mode (Level 0).

4. **Executing the Shred**
   - Click the **action button** (e.g., “Destroy It!”) to start shredding.  
   - The application performs multiple overwrites of the selected file to ensure it cannot be recovered.

5. **Completion & Confirmation**
   - Once finished, a **confirmation message** appears (“Done!”), and the file is permanently removed.  
   - Settings are saved automatically for future sessions.

> ⚠️ **Important:** Files shredded with this application **cannot be recovered**. Use with caution.

---
