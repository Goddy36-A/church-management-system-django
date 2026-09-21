"""
Seed the database with clearly-labeled, fictional demo data for the
Church Management Information System (Mbarara City academic prototype).

Usage:
    python manage.py seed_demo            # seeds (idempotent — safe to re-run)
    python manage.py seed_demo --reset    # deletes existing demo rows first
"""

import random
from datetime import date, timedelta

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import Role, RoleName, User
from attendance.models import AttendanceRecord, AttendanceSession, ServiceType
from communications.models import (
    Announcement, AnnouncementAudience, FollowUp, FollowUpReason, FollowUpStatus,
)
from coresys.models import EfficiencyMetric, SurveyQuestion, SurveyResponse
from events.models import Event, EventParticipant, EventStatus
from finance.models import Contribution, ContributionCategory
from members.models import (
    Department, Group, GroupMember, Member, MembershipStatus, Ministry,
)

FIRST_NAMES = [
    "Alinda", "Byaruhanga", "Kyomuhendo", "Tumusiime", "Ninsiima", "Ainembabazi",
    "Kwikiriza", "Ariho", "Natukunda", "Mugisha", "Atuhaire", "Turyahabwe",
    "Kobusingye", "Asiimwe", "Bwambale", "Kirabo", "Nabukenya", "Ssekandi",
    "Namuli", "Okello", "Achieng", "Kato", "Nabirye", "Muhwezi",
]
LAST_NAMES = [
    "Karungi", "Byamukama", "Tumwine", "Kabagambe", "Nuwagaba", "Twinomujuni",
    "Mbabazi", "Katusiime", "Rukundo", "Kansiime", "Bagenda", "Nakato",
    "Mukasa", "Namara", "Tugume", "Basemera",
]

FICTION_NOTICE = "DEMO DATA — fictional, for academic evaluation purposes only."
DEMO_PASSWORD = "Demo@12345"


def random_name_pair(used):
    while True:
        pair = (random.choice(FIRST_NAMES), random.choice(LAST_NAMES))
        if pair not in used:
            used.add(pair)
            return pair


class Command(BaseCommand):
    help = "Seed the database with fictional, clearly-labeled demo data."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset", action="store_true",
            help="Delete existing seeded data before re-seeding.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["reset"]:
            self.stdout.write("Clearing existing data...")
            AttendanceRecord.objects.all().delete()
            AttendanceSession.objects.all().delete()
            EventParticipant.objects.all().delete()
            Event.objects.all().delete()
            Announcement.objects.all().delete()
            FollowUp.objects.all().delete()
            Contribution.objects.all().delete()
            ContributionCategory.objects.all().delete()
            SurveyResponse.objects.all().delete()
            SurveyQuestion.objects.all().delete()
            EfficiencyMetric.objects.all().delete()
            GroupMember.objects.all().delete()
            Group.objects.all().delete()
            User.objects.filter(is_superuser=False).delete()
            Member.objects.all().delete()
            Ministry.objects.all().delete()
            Department.objects.all().delete()

        self.stdout.write("Creating roles...")
        roles = {}
        for name in RoleName.ALL:
            role, _ = Role.objects.get_or_create(
                name=name, defaults={"description": RoleName.LABELS.get(name, name)}
            )
            roles[name] = role

        self.stdout.write("Creating ministries...")
        ministry_names = ["Youth", "Men", "Women", "Children", "Worship", "Evangelism", "Prayer", "Ushering Media"]
        ministries = [
            Ministry.objects.get_or_create(
                name=name, defaults={"description": f"{name} ministry. {FICTION_NOTICE}"}
            )[0]
            for name in ministry_names
        ]

        self.stdout.write("Creating departments...")
        department_names = ["Finance", "Facilities", "Communications", "Welfare"]
        departments = [
            Department.objects.get_or_create(
                name=name, defaults={"description": f"{name} department. {FICTION_NOTICE}"}
            )[0]
            for name in department_names
        ]

        self.stdout.write("Creating groups/cells...")
        group_names = ["Kakoba Cell", "Nyamitanga Cell", "Kamukuzi Cell", "Biharwe Cell"]
        groups = [
            Group.objects.get_or_create(
                name=name,
                defaults={"meeting_day": "Wednesday evenings", "location": "Member homes, Mbarara"},
            )[0]
            for name in group_names
        ]

        self.stdout.write("Creating fictional members...")
        statuses_pool = (
            [MembershipStatus.ACTIVE] * 6 + [MembershipStatus.NEW] * 2
            + [MembershipStatus.INACTIVE] * 2 + [MembershipStatus.TRANSFERRED]
        )
        if Member.objects.count() < 40:
            used_names = set()
            for i in range(40):
                first, last = random_name_pair(used_names)
                dob = date.today() - timedelta(days=random.randint(18 * 365, 75 * 365))
                joined = date.today() - timedelta(days=random.randint(30, 365 * 5))
                Member.objects.create(
                    member_no=f"MBR-{i + 1:04d}",
                    first_name=first,
                    last_name=last,
                    gender=random.choice(["male", "female"]),
                    date_of_birth=dob,
                    phone=f"07{random.randint(10000000, 99999999)}",
                    email=f"{first.lower()}.{last.lower()}{i}@example.org",
                    physical_address="Mbarara City, Uganda",
                    date_joined=joined,
                    membership_status=random.choice(statuses_pool),
                    baptism_status=random.choice(["baptized", "not_baptized"]),
                    marital_status=random.choice(["single", "married", "widowed"]),
                    occupation=random.choice(
                        ["Teacher", "Trader", "Farmer", "Student", "Nurse", "Driver", "Civil Servant"]
                    ),
                    ministry=random.choice(ministries) if random.random() > 0.2 else None,
                    department=random.choice(departments) if random.random() > 0.6 else None,
                    notes=FICTION_NOTICE,
                )
        members = list(Member.objects.all())

        # Assign ministry/department leaders
        for ministry in ministries:
            if not ministry.leader_id and members:
                ministry.leader = random.choice(members)
                ministry.save()
        for department in departments:
            if not department.leader_id and members:
                department.leader = random.choice(members)
                department.save()

        self.stdout.write("Assigning group memberships...")
        for group in groups:
            if not group.memberships.exists() and members:
                group.leader = random.choice(members)
                group.save()
                for member in random.sample(members, k=min(6, len(members))):
                    GroupMember.objects.get_or_create(group=group, member=member)

        self.stdout.write("Creating demo user accounts...")

        def create_user(username, email, full_name, role_name, member_link=None):
            if User.objects.filter(username=username).exists():
                return User.objects.get(username=username)
            user = User(
                username=username, email=email, full_name=full_name,
                role=roles[role_name], member=member_link,
                # super_admin also gets Django admin (/django-admin/) access,
                # matching their role's system-wide reach in the app itself.
                is_staff=(role_name == RoleName.SUPER_ADMIN),
                is_superuser=(role_name == RoleName.SUPER_ADMIN),
            )
            user.set_password(DEMO_PASSWORD)
            user.save()
            return user

        create_user("superadmin", "superadmin@example.org", "Grace Ahumuza", RoleName.SUPER_ADMIN)
        create_user("admin", "admin@example.org", "Peter Rwabwogo", RoleName.ADMIN)
        create_user("pastor", "pastor@example.org", "Pastor Daniel Mugume", RoleName.PASTOR)
        create_user("finance", "finance@example.org", "Sarah Nabatanzi", RoleName.FINANCE_OFFICER)
        create_user("youthleader", "youthleader@example.org", "James Katsigazi", RoleName.MINISTRY_LEADER)
        if members:
            demo_member = members[0]
            create_user("member1", "member1@example.org", demo_member.full_name,
                        RoleName.MEMBER, member_link=demo_member)

        self.stdout.write("Creating attendance sessions (last 12 weeks of Sunday services)...")
        if AttendanceSession.objects.count() < 10 and members:
            for weeks_ago in range(12, 0, -1):
                session_date = date.today() - timedelta(weeks=weeks_ago)
                session = AttendanceSession.objects.create(
                    title=f"Sunday Service - {session_date.strftime('%d %b %Y')}",
                    service_type=ServiceType.SUNDAY_SERVICE,
                    session_date=session_date,
                    notes=FICTION_NOTICE,
                )
                attendees = random.sample(
                    members, k=random.randint(int(len(members) * 0.4), int(len(members) * 0.85))
                )
                for member in attendees:
                    AttendanceRecord.objects.create(session=session, member=member, present=True)
                for _ in range(random.randint(0, 3)):
                    AttendanceRecord.objects.create(
                        session=session, member=None, present=True, is_visitor=True,
                        visitor_name=f"Visitor {random.randint(100, 999)}",
                    )

        self.stdout.write("Creating events...")
        if Event.objects.count() < 3 and members:
            event_defs = [
                ("Annual Youth Conference", "youth_conference", 10, "Church Main Hall"),
                ("Community Outreach - Nyamitanga", "outreach", 25, "Nyamitanga Trading Center"),
                ("Women's Prayer Retreat", "retreat", 45, "Lake View Retreat Center"),
            ]
            for title, etype, days_ahead, location in event_defs:
                event = Event.objects.create(
                    title=title, description=f"{title}. {FICTION_NOTICE}", event_type=etype,
                    start_date=date.today() + timedelta(days=days_ahead),
                    location=location, max_participants=100, status=EventStatus.PLANNED,
                )
                for member in random.sample(members, k=min(15, len(members))):
                    EventParticipant.objects.create(
                        event=event, member=member, attended=random.random() > 0.7
                    )

        self.stdout.write("Creating announcements...")
        if Announcement.objects.count() < 3:
            announcements = [
                ("Sunday Service Time Change",
                 "Starting next month, the second service will begin at 10:30 AM instead of 11:00 AM.", "high"),
                ("Building Fund Update",
                 "Thank you for your continued generosity towards the new sanctuary building fund.", "normal"),
                ("Youth Camp Registration Open",
                 "Registration for the annual youth camp is now open. Speak to your ministry leader to register.",
                 "normal"),
            ]
            for title, message, priority in announcements:
                Announcement.objects.create(
                    title=title, message=f"{message} {FICTION_NOTICE}",
                    target_audience=AnnouncementAudience.ALL,
                    priority=priority, status="published",
                )

        self.stdout.write("Creating follow-ups...")
        if FollowUp.objects.count() < 3:
            inactive_members = [m for m in members if m.membership_status == MembershipStatus.INACTIVE][:3]
            for member in inactive_members:
                FollowUp.objects.create(
                    member=member, reason=FollowUpReason.REPEATED_ABSENCE,
                    status=FollowUpStatus.PENDING, notes=FICTION_NOTICE,
                    next_followup_date=date.today() + timedelta(days=7),
                )

        self.stdout.write("Creating contribution categories and demo contributions...")
        category_names = ["Tithe", "Offering", "Building Fund", "Special Donation"]
        categories = [ContributionCategory.objects.get_or_create(name=name)[0] for name in category_names]

        if Contribution.objects.count() < 20 and members:
            for _ in range(60):
                Contribution.objects.create(
                    member=random.choice(members) if random.random() > 0.1 else None,
                    category=random.choice(categories),
                    amount=random.choice([5000, 10000, 20000, 50000, 100000]),
                    contribution_date=date.today() - timedelta(days=random.randint(0, 300)),
                    payment_method=random.choice(["cash", "mobile_money", "bank"]),
                    notes=FICTION_NOTICE,
                )

        self.stdout.write("Creating research evaluation questions and demo responses...")
        admin_efficiency_qs = [
            "The system reduces the time required to manage member records.",
            "The system makes member information easier to retrieve.",
            "The system improves attendance management.",
            "The system reduces paperwork.",
            "The system improves report generation.",
            "The system improves data accuracy.",
        ]
        engagement_qs = [
            "The system improves communication between church leadership and members.",
            "The system makes church events easier to access.",
            "The system encourages participation.",
            "The system improves follow-up of members.",
            "The system improves access to church information.",
        ]

        questions = []
        for i, text in enumerate(admin_efficiency_qs):
            q, _ = SurveyQuestion.objects.get_or_create(
                text=text, defaults={"dimension": "administrative_efficiency", "display_order": i}
            )
            questions.append(q)
        for i, text in enumerate(engagement_qs):
            q, _ = SurveyQuestion.objects.get_or_create(
                text=text, defaults={"dimension": "member_engagement", "display_order": i}
            )
            questions.append(q)

        if SurveyResponse.objects.count() < 10:
            for q in questions:
                for _ in range(random.randint(8, 15)):
                    SurveyResponse.objects.create(
                        question=q,
                        score=random.choices([1, 2, 3, 4, 5], weights=[1, 2, 4, 6, 5])[0],
                        is_demo_data=True, respondent_role="demo",
                    )

        self.stdout.write("Adding sample administrative efficiency baseline metrics...")
        if EfficiencyMetric.objects.count() < 3:
            sample_metrics = [
                ("Member registration time (minutes)", 15, 4),
                ("Attendance recording time (minutes)", 30, 8),
                ("Report generation time (minutes)", 120, 10),
            ]
            for name, prev, cur in sample_metrics:
                EfficiencyMetric.objects.create(
                    metric_name=name, previous_process_value=prev, cmis_process_value=cur,
                    unit="minutes", notes=FICTION_NOTICE,
                )

        self.stdout.write(self.style.SUCCESS("\nSeed complete."))
        self.stdout.write(f"Demo login accounts (password for all: {DEMO_PASSWORD}):")
        self.stdout.write("  superadmin / admin / pastor / finance / youthleader / member1")
