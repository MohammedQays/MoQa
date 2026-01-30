import pywikibot
import json
import re

SITE_EN = pywikibot.Site('en', 'wikipedia')
SITE_AR = pywikibot.Site('ar', 'wikipedia')

SOURCE_MODULE = "Module:Team_appearances_list/data"
TARGET_MODULE = "وحدة:Team appearances list/data"

JSON_PAGE = "مستخدم:Mohammed Qays/game.json"

EDIT_SUMMARY = "[[وب:بوت|بوت]]: تحديث"

def load_json_translations():
    page = pywikibot.Page(SITE_AR, JSON_PAGE)
    return json.loads(page.text)


def arabize_lua_pairs(text, names):
    def repl(match):
        key = match.group(1)
        val = match.group(2)

        ar_key = names.get(key, key)
        ar_val = names.get(val, val)

        return f'["{ar_key}"] = "{ar_val}"'

    pattern = r'\["([^"]+)"\]\s*=\s*"([^"]+)"'
    return re.sub(pattern, repl, text)

def arabize_lua_keys(text, names):
    def repl(match):
        key = match.group(1)
        ar_key = names.get(key, key)
        return f'["{ar_key}"]'

    pattern = r'\["([^"]+)"\]'
    return re.sub(pattern, repl, text)

def arabize_regions(text, names):
    for en, ar in names.items():
        text = text.replace(f"-----{en}-----", f"----- {ar} -----")
    return text

def main():
    source_page = pywikibot.Page(SITE_EN, SOURCE_MODULE)
    lua_text = source_page.text
    names = load_json_translations()
    lua_text = arabize_lua_pairs(lua_text, names)
    lua_text = arabize_lua_keys(lua_text, names)
    lua_text = arabize_regions(lua_text, names)
    target_page = pywikibot.Page(SITE_AR, TARGET_MODULE)
    target_page.text = lua_text
    target_page.save(EDIT_SUMMARY)

if __name__ == "__main__":
    main()
