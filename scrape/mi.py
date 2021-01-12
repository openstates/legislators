from spatula.pages import HtmlListPage
from spatula.selectors import CSS
from common import Person


def split_name(name):
    commas = name.count(",")
    if commas == 0:
        first, last = name.split(" ", 1)  # special case for one legislator right now
    elif commas == 1:
        last, first = name.split(", ")
    else:
        raise ValueError(name)
    return {"given_name": first, "family_name": last, "name": f"{first} {last}"}


def ord_suffix(str_num):
    num = int(str_num) % 100
    if 4 <= num <= 20:
        return "th"
    return {1: "st", 2: "nd", 3: "rd"}.get(num % 10, "th")


class SenList(HtmlListPage):
    source = "https://senate.michigan.gov/senatorinfo_list.html"
    selector = CSS(".table tbody tr", num_items=38)
    PARTY_MAP = {"Rep": "Republican", "Dem": "Democratic"}

    def process_item(self, item):
        member, party, district, contact_link, phone, office = item.getchildren()

        name = member.text_content()
        district = district.text_content()

        # skip vacant districts
        if "Interim District" in name:
            self.skip()

        # each of these <td> have a single link
        leg_url = CSS("a").match_one(member).get("href")
        contact_url = CSS("a").match_one(contact_link).get("href")
        # construct this URL based on observation elsewhere on senate.michigan.gov
        image_url = f"https://senate.michigan.gov/_images/{district}{ord_suffix(district)}.jpg"

        p = Person(
            **split_name(name),
            state="mi",
            chamber="upper",
            district=district,
            party=self.PARTY_MAP[party.text],
            image=image_url,
        )
        p.capitol_office.voice = phone.text_content()
        p.capitol_office.address = office.text_content()
        p.add_source(self.source.url)
        p.add_link(leg_url)
        p.add_link(contact_url, note="Contact")
        return p