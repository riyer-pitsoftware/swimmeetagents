# Swim Tracker Sources (Ontario) — public results seeds
# Purpose: seed URLs for discovering meet results pages/PDFs.
# Rules: Only fetch pages that are public (no login), respect robots.txt, and back off politely.

## Global / authoritative hubs (best ROI)
- [swimontario_live_results_index] https://swimontario.com/liveresults/  # HY-TEK real-time results index + meet folders (HTML + PDFs). :contentReference[oaicite:0]{index=0}
- [swimming_canada_meet_results_hub] https://www.swimming.ca/events-results-hub/meet-results/  # official sanctioned meet pages with downloads. :contentReference[oaicite:1]{index=1}

## VAC — Vaughan Aquatic Club
- [vac_home_upcoming_meets] https://vaughanaquaticclub.com/  # “Upcoming Meets” section with packages/schedules (often links out). :contentReference[oaicite:2]{index=2}
- [vac_36th_roy_jacobson_sc_meet_page] https://www.swimming.ca/swim-meet/60691/  # has “Meet Results Download”. :contentReference[oaicite:3]{index=3}

## NYAC — North York Aquatic Club
- [nyac_results_page] https://www.gomotionapp.com/team/cannyac/page/events/results  # points to sanctioned results archive. :contentReference[oaicite:4]{index=4}
- [nyac_hosted_meets_page] https://www.gomotionapp.com/team/cannyac/page/events/hosted-meets  # hosted meets page (may link to packages/results). :contentReference[oaicite:5]{index=5}
- [nyac_cup_2025_meet_page] https://www.swimming.ca/swim-meet/60882/  # has “Meet Results Download” (example). :contentReference[oaicite:6]{index=6}
- [nyac_sample_public_results_pdf] https://www.gomotionapp.com/cannyac/UserFiles/Image/QuickUpload/feb-27-session-2-results-rev_059435.pdf  # example fixture-style PDF. :contentReference[oaicite:7]{index=7}

## ESWIM — Etobicoke Swim Club
- [eswim_public_pdf_example_top_cup] https://www.eswim.ca/etobicokesc/UserFiles/Image/QuickUpload/lc-pub-results_059157.pdf  # example public results PDF. :contentReference[oaicite:8]{index=8}
- [eswim_public_pdf_example_div1] https://www.eswim.ca/etobicokesc/UserFiles/Image/QuickUpload/div-1-pub-order-results_018206.pdf  # newer public results PDF. :contentReference[oaicite:9]{index=9}

## SCAR — Scarborough Swim Club
# SCAR’s site may be JS-heavy; use Swim Ontario + Swimming Canada hubs to locate meet pages/results involving SCAR.
- [scar_team_page_reference] https://www.gomotionapp.com/team/canonssc/page/system/coaches  # confirms team site exists (not necessarily results). :contentReference[oaicite:10]{index=10}
- [scar_example_in_swimontario_pdf] https://swimontario.com/liveresults/2025/OSC/PointScore0.pdf  # example PDF containing “Scarborough Swim Club (SCAR)”. :contentReference[oaicite:11]{index=11}

## OSHAC — Oshawa Aquatic Club
# Use Swim Ontario + Swimming Canada hubs to find OSHAC meet pages/results; OSHAC site is GoMotion-based.
- [oshac_home] https://www.gomotionapp.com/team/canoac/page/home :contentReference[oaicite:12]{index=12}
- [oshac_swimming_canada_hub] https://www.swimming.ca/events-results-hub/meet-results/ :contentReference[oaicite:13]{index=13}

## Example Swim Ontario meet folders (pattern examples)
# Useful for adapter development: folder-style live results with event index + entrylist/results links.
- [swimontario_example_osc_2025_folder] https://swimontario.com/liveresults/2025/OSC/ :contentReference[oaicite:14]{index=14}
- [swimontario_example_oag_2025_folder] https://swimontario.com/liveresults/2025/OAG/ :contentReference[oaicite:15]{index=15}