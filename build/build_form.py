#!/usr/bin/env python3
"""
Generate a FormCraft 3 import file (.txt) from a short form spec.

    python3 build/build_form.py spec/forms/contact.json          -> templates/forms/contact.txt
    python3 build/build_form.py spec/forms/contact.json --print  -> prints the decoded builder JSON

Import: FormCraft > Add New > Import > choose the .txt > name it > Create Form.
Then open the form once in the FormCraft editor and press Save, which recompiles
the stored HTML against the real form id. Embed with the native Elementor Shortcode
widget:  [fc id='<id>'][/fc]

The export format was reverse-engineered from a real FormCraft 3 export (Sept 2026):
  {"plugin":"FormCraft","created":<unix>,"html":"rawdeflate,<b64>","addons":"<json>",
   "builder":"rawdeflate,<b64>","meta_builder":"<json>","old_url":"<site>"}
html/builder are zlib raw-deflate (wbits=-15) then base64. addons/meta_builder are
JSON strings. Field types below are the ones present in that export; anything else
must be added in the FormCraft UI after import (or exported from a sample form first
so its markup can be added here).

Spec (JSON):
{
  "name": "Contact",
  "site_url": "https://client.co.uk",
  "recipients": "info@client.co.uk",
  "sender_name": "Client Website", "sender_email": "no-reply@client.co.uk",
  "success": "Thanks, we'll be in touch shortly.",
  "colors": {"button": "#8F0000", "button_dark": "#700000", "step": "#8F0000",
             "step_dark": "#700000", "font": "#fff", "text": "#222222",
             "field_text": "#444444", "field_bg": "#fafafa"},
  "font_family": "Inter",
  "label_style": "placeholder",       # or "floating" / "top"
  "captcha_site_key": "",             # reCAPTCHA v3 site key; secret is set in FormCraft > Add-ons, never here
  "autoresponder": {"subject": "...", "body_html": "..."},   # optional
  "fields": [
    {"type": "text",     "label": "Name",  "required": true, "width": "50%", "icon": "person"},
    {"type": "email",    "label": "Email", "required": true, "width": "50%"},
    {"type": "text",     "label": "Phone", "required": true, "width": "50%", "validate": "numbers"},
    {"type": "dropdown", "label": "Service", "width": "50%", "options": ["Option A", "Option B"]},
    {"type": "date",     "label": "Preferred date", "width": "50%", "date_format": "dd/mm/yy"},
    {"type": "textarea", "label": "Message", "rows": 4, "width": "100%"},
    {"type": "submit",   "label": "Send message", "align": "center"},
    {"type": "captcha"}
  ]
}
"""
import base64, json, os, sys, time, zlib

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")

TYPE_MAP = {"text": "oneLineText", "email": "email", "textarea": "textarea",
            "dropdown": "dropdown", "date": "datepicker", "submit": "submit",
            "captcha": "reCaptcha"}

# ---------------------------------------------------------------- codec
def enc(s: str) -> str:
    c = zlib.compressobj(9, zlib.DEFLATED, -15)
    return "rawdeflate," + base64.b64encode(c.compress(s.encode()) + c.flush()).decode()

def dec(s: str) -> str:
    assert s.startswith("rawdeflate,")
    return zlib.decompress(base64.b64decode(s[11:]), -15).decode()

# ---------------------------------------------------------------- defaults
DEFAULT_COLORS = {"button": "#a7be91", "button_dark": "#92a77f", "step": "#4488ee",
                  "step_dark": "#3b77d1", "font": "#fff", "text": "#666666",
                  "field_text": "#777", "field_bg": "#fafafa"}
MESSAGES = {"is_invalid": "Invalid", "min_char": "Min [x] characters required",
            "max_char": "Max [x] characters allowed", "max_files": "Too many files",
            "max_file_size": "Files bigger than [x] MB not allowed", "allow_email": "Invalid Email",
            "allow_url": "Invalid URL", "allow_regexp": "Invalid Expression",
            "allow_alphabets": "Only alphabets", "allow_numbers": "Only numbers",
            "allow_alphanumeric": "Should be alphanumeric",
            "failed": "Please correct the errors and try again", "success": "Message received"}
NOTIFICATION_BODY = ("<p>Hello,</p><p><br></p><p>You have received a new form submission for the form "
                     "[Form Name]. Here are the details:</p><p>[Form Content]</p><p><br></p>"
                     "<p>Page: [URL]<br>Unique ID: #[Entry ID]<br>Date: [Date]<br>Time: [Time]</p>")

# ---------------------------------------------------------------- element defaults (builder + meta_builder)
def element_defaults(f, ident):
    t = TYPE_MAP[f["type"]]
    label = f.get("label", "")
    d = {"field_width": f.get("width", "100%"), "identifier": ident, "hidden_default": False,
         "required": bool(f.get("required", False)), "main_label": label,
         "sub_label": f.get("sub_label", ""), "main_label_placeholder": f.get("placeholder", label),
         "has_sub_label": bool(f.get("sub_label"))}
    if t == "oneLineText":
        d.update({"selectedIcon": f.get("icon", ""), "readonly": False,
                  "Validation": {"allowed": f.get("validate", "")}})
    elif t == "email":
        pass
    elif t == "textarea":
        d["field_height"] = str(f.get("rows", 3))
    elif t == "dropdown":
        opts = f.get("options", [])
        d["options_list"] = "==" + label + "\n" + "\n".join(opts)
        d["optionsListShow"] = [{"value": "", "show": label}] + [{"value": o, "show": o} for o in opts]
    elif t == "datepicker":
        d.update({"dateLang": "en", "dateFormat": f.get("date_format", "dd/mm/yy"),
                  "dateDays": [True] * 7, "minDateAlt": "", "maxDateAlt": "", "minDate": "", "maxDate": ""})
    elif t == "submit":
        d.update({"main_label": label or "Submit", "isWide": bool(f.get("wide", False)),
                  "doAnimate": False, "alignment": f.get("align", "center"), "main_label_placeholder": ""})
        d.pop("has_sub_label", None); d.pop("sub_label", None)
    elif t == "reCaptcha":
        d.update({"main_label": "Captcha", "sub_label": "captcha", "main_label_placeholder": ""})
        d.pop("has_sub_label", None)
    return d

# ---------------------------------------------------------------- html per field
def html_common(ident, i, t, d):
    parity = "odd" if i % 2 == 0 else "even"
    req = str(d["required"]).lower()
    return (f'<div data-identifier="{ident}" data-index="{i}" style="width: {d["field_width"]}" '
            f'class=" form-element form-element-{ident} options-false index-false form-element-{i} '
            f'default-false form-element-type-{t} is-required-{req} {parity} -handle">'
            f'<div class="form-element-html"><div >')

def label_open(cover, d):
    sub = "true" if d.get("has_sub_label") else "false"
    subtxt = f'<span >{d["sub_label"]}</span>' if d.get("sub_label") else ""
    return (f'<label class="{cover} field-cover "><span class="sub-label-{sub}"><span class="main-label">'
            f'<span >{d["main_label"]}</span></span><span class="sub-label">{subtxt}</span></span>'
            f'<div><span class="error"></span>')

TIP = 'data-placement="right" data-toggle="tooltip" tooltip="" data-trigger="focus" data-html="true" data-original-title=""'

def field_html(f, ident, i):
    t = TYPE_MAP[f["type"]]; d = element_defaults(f, ident); req = str(d["required"]).lower()
    ph = d.get("main_label_placeholder", "")
    out = html_common(ident, i, t, d)
    if t == "oneLineText":
        icon = d["selectedIcon"]
        out += label_open("oneLineText-cover", d)
        out += (f'<input type="text" placeholder="{ph}" make-read-only="false" data-field-id="{ident}" name="{ident}[]" '
                f'data-min-char="" data-max-char="" data-val-type="{d["Validation"]["allowed"]}" data-regexp="" '
                f'data-is-required="{req}" data-allow-spaces="" class="validation-lenient" {TIP} data-input-mask="" '
                f'data-mask-placeholder=""><i class="formcraft-icon formcraft-icon-type-{icon}">{icon}</i></div></label>')
    elif t == "email":
        out += label_open("email-cover", d)
        out += (f'<input placeholder="{ph}" data-field-id="{ident}" type="text" data-val-type="email" make-read-only="" '
                f'data-is-required="{req}" name="{ident}" class="validation-lenient" {TIP}>'
                f'<i class="formcraft-icon">email</i></div></label>')
    elif t == "textarea":
        out += label_open("textarea-cover", d)
        out += (f'<textarea data-field-id="{ident}" placeholder="{ph}" class="validation-lenient" name="{ident}" value="" '
                f'rows="{d["field_height"]}" data-min-char="" data-max-char="" data-is-required="{req}" {TIP}></textarea>'
                f'<div class="count-"><span class="current-count">0</span> / <span class="max-count "></span></div></div></label>')
    elif t == "dropdown":
        opts = "".join(f'<option value="{o["value"]}" class=" ">{o["show"]}</option>' for o in d["optionsListShow"])
        out += label_open("dropdown-cover", d).replace('dropdown-cover field-cover ', 'dropdown-cover field-cover autocomplete-type- has-input')
        out += (f'<select data-is-required="{req}" class="validation-lenient" data-field-id="{ident}" name="{ident}" '
                f'{TIP.replace("focus", "hover")}>{opts}</select><input type="text"></div></label>')
    elif t == "datepicker":
        days = json.dumps({str(k): True for k in range(7)}).replace('"', "&quot;")
        out += label_open("datepicker-cover", d)
        out += (f'<input autocomplete="off" data-field-id="{ident}" placeholder="{ph}" type="text" class="validation-lenient    hasDatepicker" '
                f'data-is-required="{req}" datepicker="" data-date-min-range="" data-date-format="{d["dateFormat"]}" '
                f'data-date-days="{days}" data-date-min="" data-date-min-alt="" data-date-max-alt="" data-date-max="" '
                f'data-date-lang="en" name="{ident}" {TIP}><i class="formcraft-icon">date_range</i></div></label>')
    elif t == "submit":
        out += (f'<div class="align-{d["alignment"]} wide-{str(d["isWide"]).lower()} submit-cover field-cover">'
                f'<button type="submit" class="button submit-button"><span class="text ">{d["main_label"]}</span>'
                f'<span class="spin-cover"><i style="color:" class="loading-icon icon-cog animate-spin"></i></span></button></div>'
                f'<div class="submit-response "></div><label ><input type="text" class="required_field" name="website" autocomplete="maple-syrup-pot"></label>')
    elif t == "reCaptcha":
        key = f.get("site_key", "")
        out += (f'<div data-site-key="{key}" class="captcha-placeholder ">reCaptcha v3</div>'
                f'<input type="hidden" class="recaptcha-token " name="recaptcha-token">')
    out += "</div></div>\n</div>"
    return out

def style_block(c, font_family, fid):
    b, bd, s, sd, fo, tx, ft, bg = (c["button"], c["button_dark"], c["step"], c["step_dark"], c["font"],
                                     c["text"], c["field_text"], c["field_bg"])
    F = f".formcraft-css .fc-form.fc-form-{fid} .form-element"
    return f"""<style scoped="scoped" >
@media (max-width : 480px) {{ .fc_modal-dialog-{fid} .fc-pagination-cover .fc-pagination {{ background-color: none !important; }} }}
{F} .submit-cover .submit-button, {F} .fileupload-cover .button-file, {F} .field-cover .button,
.formcraft-datepicker .ui-datepicker-header, .formcraft-datepicker .ui-datepicker-title {{ background: {b}; color: {fo}; }}
.formcraft-datepicker td .ui-state-active, .formcraft-datepicker td .ui-state-hover, {F} .slider-cover .ui-slider-range {{ background: {b}; }}
#ui-datepicker-div.formcraft-datepicker .ui-datepicker-header, .formcraft-css .fc-form .field-cover>div.full hr {{ border-color: {bd}; }}
#ui-datepicker-div.formcraft-datepicker .ui-datepicker-prev:hover, #ui-datepicker-div.formcraft-datepicker .ui-datepicker-next:hover,
#ui-datepicker-div.formcraft-datepicker select.ui-datepicker-month:hover, #ui-datepicker-div.formcraft-datepicker select.ui-datepicker-year:hover {{ background-color: {bd}; }}
.formcraft-css .fc-pagination>div.active .page-number, .formcraft-css .form-cover-builder .fc-pagination>div:first-child .page-number {{ background-color: {s}; color: {fo}; }}
#ui-datepicker-div.formcraft-datepicker table.ui-datepicker-calendar th, #ui-datepicker-div.formcraft-datepicker table.ui-datepicker-calendar td.ui-datepicker-today a,
{F} .star-cover label, html .formcraft-css .fc-form.label-floating .form-element .field-cover.has-focus>span, {F} .customText-cover a, .formcraft-css .prev-next>div span:hover {{ color: {b}; }}
{F} .customText-cover a:hover {{ color: {bd}; }}
html .formcraft-css .fc-form.fc-form-{fid}.label-floating .form-element .field-cover > span {{ color: {tx}; }}
html .formcraft-css .fc-form .final-success .final-success-check {{ border: 2px solid {tx}; }}
{F} .field-cover input[type="text"], {F} .field-cover input[type="email"], {F} .field-cover input[type="password"], {F} .field-cover input[type="tel"],
{F} .field-cover textarea, {F} .field-cover select, {F} .field-cover .time-fields-cover, {F} .field-cover .awesomplete ul {{ color: {ft}; }}
{F} .field-cover input[type="text"], {F} .field-cover input[type="password"], {F} .field-cover input[type="email"], {F} .field-cover input[type="radio"],
{F} .field-cover input[type="checkbox"], {F} .field-cover input[type="tel"], {F} .field-cover select, {F} .field-cover textarea {{ background-color: {bg}; }}
{F} .field-cover input[type="radio"]:checked, {F} .field-cover input[type="checkbox"]:checked {{ border-color: {bd}; background: {b}; }}
{F} .star-cover label .star {{ text-shadow: 0px 1px 0px {bd}; }}
{F} .slider-cover .ui-slider-range {{ box-shadow: 0px 1px 1px {bd} inset; }}
{F} .fileupload-cover .button-file {{ border-color: {bd}; }}
{F} .form-element-html input[type="password"]:focus, {F} .form-element-html input[type="email"]:focus, {F} .form-element-html input[type="tel"]:focus,
{F} .form-element-html input[type="text"]:focus, {F} .form-element-html textarea:focus, {F} .form-element-html select:focus {{ border-color: {b}; }}
{F} .form-element-html .field-cover .is-read-only:focus {{ border-color: #ccc; }}
.formcraft-css .fc-form.fc-form-{fid} {{ font-family: {font_family}; }}
@media (max-width : 480px) {{ html .dedicated-page, html .dedicated-page .formcraft-css .fc-pagination > div.active {{ background: none; }} }}
</style>"""

# ---------------------------------------------------------------- build
def build(spec, form_id=1):
    c = {**DEFAULT_COLORS, **spec.get("colors", {})}
    font_family = spec.get("font_family", "inherit")
    label_style = spec.get("label_style", "placeholder")
    fields = spec["fields"]
    if not any(f["type"] == "submit" for f in fields):
        fields = fields + [{"type": "submit", "label": "Submit"}]
    for f in fields:
        if f["type"] == "captcha" and spec.get("captcha_site_key"):
            f.setdefault("site_key", spec["captcha_site_key"])
        if f["type"] not in TYPE_MAP:
            sys.exit(f"unsupported field type '{f['type']}': build it in the FormCraft UI after import")

    idents = [f"field{i+1}" for i in range(len(fields))]
    meta_fields, form_elements, html_fields = [], [], []
    for i, (f, ident) in enumerate(zip(fields, idents)):
        t = TYPE_MAP[f["type"]]; d = element_defaults(f, ident)
        meta_fields.append({"identifier": ident, "type": t, "elementDefaults": d, "page": 1, "isPayment": False})
        form_elements.append({"element": f"<div compile='fieldHTMLTemplate[\"{t}\"]'></div>", "restrict": False,
                              "identifier": ident, "type": t,
                              "elementOptions": f"<div compile='fieldOptionTemplate[\"{t}\"]'></div>",
                              "elementDefaults": d})
        html_fields.append(field_html(f, ident, i))

    notifications = {"_method": "php", "form_layout": False, "email_body": NOTIFICATION_BODY,
                     "email_subject": "[Form Name] - New Form Submission", "showTip": True,
                     "general_sender_name": spec.get("sender_name", spec["name"]),
                     "general_sender_email": spec.get("sender_email", spec["recipients"].split(",")[0].strip()),
                     "recipients": spec["recipients"]}
    ar = spec.get("autoresponder") or {}
    autoresponder = {"email_subject": ar.get("subject", ""), "email_body": ar.get("body_html", "")}
    messages = {**MESSAGES, "success": spec.get("success", MESSAGES["success"])}
    config = {"Logic": spec.get("logic", []), "messages": {}, "autoresponder": autoresponder,
              "notifications": notifications, "page_names": ["Step 1"],
              "color_scheme_button": c["button"], "color_scheme_step": c["step"], "color_scheme_font": c["font"],
              "form_name": spec["name"], "Messages": messages,
              "showOptions": False, "showAddons": False, "showStyling": False, "showLogic": False, "showAddField": True,
              "decimal_separator": ".", "thousand_separator": "", "font_color": c["text"],
              "field_font_color": c["field_text"], "webhook_method": "POST", "font_family": font_family,
              "color_field_background": c["field_bg"], "color_scheme_button_dark": c["button_dark"],
              "color_scheme_step_dark": c["step_dark"], "form_background_type": "none", "showFields": False}

    builder = {"Config": config, "FormElements": form_elements, "Options": {},
               "form_background": "none", "form_background_type": "white", "label_style": label_style,
               "form_width": spec.get("width", "100%"), "form_frame": "hidden", "form_field_border": "visible",
               "font_size": 100, "nextText": "Next", "prevText": "Previous", "form_internal_alignment": "left",
               "form_background_color": "", "form_asterisk": True, "elements_counter": len(fields),
               "TestEmails": ""}
    meta_builder = {"fields": meta_fields, "config": config, "emailRecipients": spec["recipients"], "pageCount": 1}

    style = f"""width: {spec.get("width", "100%")}; color: {c["text"]}; font-size: 100%; background: none"""
    html = (f'<div class="fc-pagination-cover fc-pagination-1"><div class="fc-pagination width-100">'
            f'<div class="pagination-trigger " data-index="0"><span class="page-number"><span >1</span></span>'
            f'<span class="page-name ">Step 1</span></div></div></div>\n'
            + style_block(c, font_family, form_id) +
            f'\n<div class="form-cover"><form data-auto-scroll="" data-no-message-redirect="" data-thousand="" data-decimal="." '
            f'data-delay="" data-id="{form_id}" class="fc-form fc-form-{form_id} align- fc-temp-class save-form- dont-submit-hidden- '
            f'icons-hide- disable-enter- label-{label_style} field-border-visible frame-hidden remove-asterisk-true '
            f'field-alignment-left   options-fade" style="{style}">'
            f'<div class="form-page form-page-0" data-index="0"><div class="form-page-content     ">'
            + "".join(html_fields) +
            f'</div></div></form><div class="prev-next prev-next-1" style="{style}"><div>'
            f'<span class="inactive page-prev "><i class="formcraft-icon">keyboard_arrow_left</i>Previous</span></div>'
            f'<div><span class="page-next ">Next<i class="formcraft-icon">keyboard_arrow_right</i></span></div></div></div>')

    addons = {}
    if spec.get("captcha_site_key"):
        addons["Captcha"] = {"site_key": spec["captcha_site_key"], "secret_key": "", "score": ""}

    return {"plugin": "FormCraft", "created": int(time.time()), "html": enc(html),
            "addons": json.dumps(addons), "builder": enc(json.dumps(builder)),
            "meta_builder": json.dumps(meta_builder), "old_url": spec.get("site_url", "")}, builder

# ---------------------------------------------------------------- cli
if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == "--scrub":
        # strip SMTP credentials and captcha secret from a raw FormCraft export so it can be kept/shared
        src = sys.argv[2]; d = json.load(open(src))
        b = json.loads(dec(d["builder"])); m = json.loads(d["meta_builder"])
        for cfg in (b["Config"], m["config"]):
            for k in [k for k in cfg.get("notifications", {}) if k.startswith("smtp_")]:
                cfg["notifications"].pop(k)
        b["TestEmails"] = ""
        a = json.loads(d.get("addons") or "{}")
        if "Captcha" in a: a["Captcha"]["secret_key"] = ""
        d["builder"] = enc(json.dumps(b)); d["meta_builder"] = json.dumps(m); d["addons"] = json.dumps(a)
        out = src.replace(".txt", ".scrubbed.txt")
        json.dump(d, open(out, "w"), separators=(",", ":")); print("wrote", out); sys.exit()
    spec_path = sys.argv[1]
    spec = json.load(open(spec_path))
    export, builder = build(spec, form_id=int(spec.get("form_id", 1)))
    if "--print" in sys.argv:
        print(json.dumps(builder, indent=1)); sys.exit()
    out_dir = os.path.join(ROOT, "templates", "forms"); os.makedirs(out_dir, exist_ok=True)
    slug = os.path.splitext(os.path.basename(spec_path))[0]
    out = os.path.join(out_dir, f"{slug}.txt")
    with open(out, "w") as fh:
        json.dump(export, fh, separators=(",", ":"))
    print(f"wrote {out}  ({len(spec['fields'])} fields; recipients {spec['recipients']})")
