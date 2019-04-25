from weighted_levenshtein import lev
import numpy as np
from soleadify_ml.models.directory_contact import DirectoryContact
from django.db.models import Q
from django.db.models import Count
from soleadify_ml.models.website_contact import WebsiteContact
from tqdm import tqdm
from django.core.management.base import BaseCommand
from soleadify_ml.models.website import Website
from soleadify_ml.models.website_director import WebsiteDirector


class Command(BaseCommand):
    found = 0

    def handle(self, *args, **options):
        # websites = Website.objects.raw(
        #     "select w.id, w.domain, count(distinct wc.id) from website_contacts wc "
        #     "JOIN website_locations wl on wc.website_id = wl.website_id "
        #     "JOIN category_websites cw on wc.website_id = cw.website_id "
        #     "JOIN websites w on wc.website_id = w.id "
        #     "left join ( "
        #     "select distinct website_id from website_contacts wc "
        #     "JOIN ( "
        #     "select id from lawyer_dir_part1 "
        #     "union "
        #     "select id from lawyer_dir_part2 "
        #     "union "
        #     "select id from lawyer_dir_part3 "
        #     ") doo ON doo.id = wc.id "
        #     ") doo ON doo.website_id = w.id "
        #     "where country_code = 'us' and region_code in ('ca','tx','fl','ny','il') "
        #     "and category_id IN (10368) and doo.website_id is null and ((64 & wc.score) or (32 & wc.score)) "
        #     "group by wc.website_id "
        #     "order by count(distinct wc.id) desc"
        # )
        websites = Website.objects.raw(
            "select w.id, w.domain, count(distinct  wc.id) from websites w "
            "JOIN website_locations wl on w.id = wl.website_id "
            "JOIN category_websites cw on w.id = cw.website_id "
            "JOIN website_contacts wc on w.id = wc.website_id "
            "where country_code = 'us' and category_id IN (10368) and ((64 & wc.score) or (32 & wc.score)) "
            "group by w.id "
            "having count(distinct  wc.id) < 20 "
            "order by count(distinct  wc.id) desc"
        )
        progress_bar = tqdm(desc="Processing", total=len(websites))
        for website in websites:

            progress_bar.update(1)

            filter_contact = Q(
                Q(score=WebsiteContact.score.has_matching_email) |
                Q(score=WebsiteContact.score.has_unique_email) |
                Q(score=WebsiteContact.score.has_unique_phone)
            )

            website_contacts = WebsiteContact.objects. \
                filter(website_id=website.id). \
                filter(filter_contact)

            if len(website_contacts) < 2:
                continue

            query = Q()
            for website_contact in website_contacts:
                if website_contact.first_name and website_contact.last_name:
                    first_and_last_name_query = Q(
                        first_name=website_contact.first_name,
                        last_name=website_contact.last_name,
                        organization_key__isnull=False,
                    )
                    query.add(first_and_last_name_query, Q.OR)

            if len(query):
                organization_keys = DirectoryContact.objects.values_list('organization_key'). \
                                        annotate(dcount=Count('name', distinct=True)). \
                                        filter(query).exclude(organization_key__isnull=True).order_by('-dcount')[:3]
                delete_costs = np.zeros(128, dtype=np.float64)

                print("website_id: %s, domain: %s, website_contacts: %s" %
                      (website.id, website.domain, len(website_contacts)))

                for organization_key in organization_keys:

                    if organization_key[1] / len(website_contacts) < 0.03:
                        break

                    website_director = None
                    head = website.domain.partition('.')[0]
                    lev_cost = 10
                    try:
                        if len(head) > len(organization_key[0]):
                            lev_cost = lev(head, organization_key[0], delete_costs=delete_costs)
                        else:
                            lev_cost = lev(organization_key[0], head, delete_costs=delete_costs)
                    except:
                        pass

                    if organization_key[1] > 5 and len(website_contacts) > 5 and \
                            (organization_key[1] / len(website_contacts)) > 0.1:
                        website_director = WebsiteDirector(organization_key=organization_key[0],
                                                           website_id=website.id)
                        print("organization_key: %s, matching_contacts: %s, lev: %s, type: %s" %
                              (organization_key[0], organization_key[1], lev_cost, 1))
                    elif (organization_key[1] / len(website_contacts)) > 0.3 and lev_cost <= 2:
                        website_director = WebsiteDirector(organization_key=organization_key[0],
                                                           website_id=website.id)
                        print("organization_key: %s, matching_contacts: %s, lev: %s, type: %s" %
                              (organization_key[0], organization_key[1], lev_cost, 2))

                    if website_director:
                        WebsiteDirector.objects.bulk_create([website_director], ignore_conflicts=True)
                        # break

        progress_bar.close()
