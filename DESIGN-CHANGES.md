# Portfolio Design Changes — Sync Document

Use this file to replicate the following changes in the design tool.

---

## 1. Email Updated

**Old:** `hello@deepshikha.design` (and `you@email.com`)
**New:** `deepshikha.ranjan10@gmail.com`

Update all email references across the site to the new address.

---

## 2. Projects Section — Updated with Real Behance Projects

Replace the placeholder `projDefs` array with the following **7 projects** in this exact order:

| # | Title | Description | Tags | Behance Link | Cover Image |
|---|-------|-------------|------|-------------|-------------|
| 1 | Spatial UI for a Car Booking Platform | Designing an immersive spatial interface for seamless car booking experiences. | Spatial UI · UX | https://www.behance.net/gallery/252156661/Spatial-UI-for-a-Car-Booking-Platfrom | `Spatial UI for a Car Booking Platfrom.jpeg` (in uploads/) |
| 2 | Fashion Clothing App Design | A stylish mobile app experience for browsing & shopping fashion. | UI · Mobile | https://www.behance.net/gallery/252092187/Fashion-Clothing-App-Design | `Fabrikaa-Fashion App Prototype with Gamified User Experience.jpeg` (in uploads/) |
| 3 | AI Enhanced Customer Support Platform | Streamlining customer support with AI-powered interactions & smart workflows. | AI · UX · Web | https://www.behance.net/gallery/246485079/AI-Enhanced-Customer-Support-Platform | *(none yet)* |
| 4 | Fintech app redesign | Rethinking onboarding & portfolio for a savings app. | UX · Mobile | https://www.behance.net/deepshiranjan4 | *(none yet)* |
| 5 | Healthcare app for elders | Larger targets, calmer flows, fewer dead ends. | UX Research · UI | https://www.behance.net/deepshiranjan4 | *(none yet)* |
| 6 | Government portal concept | Making a required service feel respectful to use. | UX · Web | https://www.behance.net/deepshiranjan4 | *(none yet)* |
| 7 | Food delivery UI kit | A small, consistent component & colour system. | UI · Design system | https://www.behance.net/deepshiranjan4 | *(none yet)* |

- Project #1 is the **featured** project (large card).
- Projects #2–7 appear in the grid below.
- Each project links to its **individual Behance project page** (not the profile).
- The placeholder annotation text ("placeholder links — swap each card's URL...") should be **removed**.

---

## 3. Journey Section — Selected Step Style

**Old:** Selected step had a `3px dashed #FF6F61` (red dotted) border overlay.

**New:** Replace with:
- **Border:** `2.5px solid` using the step's own color (not hardcoded red)
- **Glow:** `box-shadow: 0 0 14px {step-color}44, 0 4px 18px rgba(0,0,0,0.08)`
- **Tint:** `background: {step-color}0a` (very subtle color fill)

This means each step highlights in its own theme color (blue for Law college, green for Law degree, purple for Advocate, etc.).

---

## 4. Journey Section — Number Badge z-index

**Issue:** The selection border overlay was covering the numbered circle badge (01, 02, etc.) on each step card.

**Fix:** Add `z-index: 1` to the number badge element so it always renders above the selection overlay.

---

## 5. Project Cards — Image Slot Editing UI Visible

**Issue:** The image-slot component shows editing UI text ("drag the photo to reposition · slider to zoom & crop") on project cover images. This editing overlay should be hidden on the deployed/shared version — it's meant for the design tool only, not for visitors.

**Fix:** Ensure the image-slot's editing controls (reframe mode, zoom slider, reposition drag) are disabled or hidden when the site is viewed outside the design editor.

---

## 6. Home Section — Removed Portrait Editing Controls

**Issue:** When a portrait photo is uploaded on the home page, the design tool's editing UI was visible to visitors — a zoom slider, "Change" button, and the text "drag the photo to reposition · slider to zoom & crop".

**Fix:** Removed the entire editing controls block (the `<sc-if>` wrapping the zoom slider, change button, and instruction text). The portrait image now displays cleanly without any editing UI overlay.

---

## Summary of files changed

- `index.html` — all changes above (projects, email, styles)
- `uploads/Spatial UI for a Car Booking Platfrom.jpeg` — project cover image (added)
- `uploads/Fabrikaa-Fashion App Prototype with Gamified User Experience.jpeg` — project cover image (added)
