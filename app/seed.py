from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from .models import Customer, Inquiry, Job, Crew, Equipment, Quote, QuoteLine, Assignment, ActivityEvent


def business_date(instant=None):
    return (instant or datetime.now(ZoneInfo("America/Toronto"))).astimezone(ZoneInfo("America/Toronto")).date()


def seed_workspace(session, workspace_id, today):
    def add(model, **values):
        record = model(workspace_id=workspace_id, **values)
        session.add(record)
        session.flush()
        return record

    customers = [add(Customer, name=name, contact=contact, email=email) for name, contact, email in [
        ("Northline Construction", "Alex Morgan", "alex@northline.example"),
        ("Cedar Ridge Developments", "Jordan Lee", "jordan@cedarridge.example"),
        ("Lakeside Civil Works", "Taylor Chen", "taylor@lakeside.example"),
    ]]
    crews = [add(Crew, name=f"Crew {name}", description=desc) for name, desc in [
        ("Alpha", "4 people · Field operations"), ("Bravo", "3 people · Site services"), ("Charlie", "4 people · Field operations")]]
    equipment = [add(Equipment, name=name, description=desc) for name, desc in [
        ("Rig 01", "Primary drilling unit"), ("Rig 02", "Secondary drilling unit"), ("Service 03", "Site support unit")]]
    for index, (title, site, service) in enumerate([
        ("Cedar Ridge access road", "42 Cedar Ridge Lane, Muskoka (fictional)", "Site preparation"),
        ("Northline foundation project", "18 Quarry Road, Barrie (fictional)", "Drilling services"),
        ("Lakeside utility corridor", "7 Lakeside Drive, Orillia (fictional)", "Site services"),
    ]):
        customer = customers[(index + 1) % 3]
        start, end = today + timedelta(days=7 + index * 3), today + timedelta(days=8 + index * 3)
        add(Inquiry, customer_id=customer.id, subject=f"Quote request — {title}", sample_key=f"example-{index + 1}",
            body=f"Hi Frank's team,\n\nWe are planning {title.lower()} at {site}. Could you prepare an estimate for {service.lower()}? We are hoping for {start:%B %d}–{end:%B %d}. Please let us know your availability and what information you need.\n\nThanks,\n{customer.contact}\n\nFictional inquiry for demonstration.",
            brief=dict(customer_id=customer.id, title=title, site=site, service=service,
                       requested_start=start.isoformat(), requested_end=end.isoformat(),
                       missing_information=["Confirm site access with the customer", "Review scope before final pricing"]))
    for index, (title, status, offset, cents) in enumerate([
        ("Granite Point expansion", "in_progress", 0, 1845000),
        ("Birchwood access road", "scheduled", 1, 1275000),
        ("Westhaven site preparation", "scheduled", 3, 960000),
        ("Pine Valley foundation", "quoted", 5, 1525000),
        ("Maple Creek servicing", "draft", 6, 825000),
        ("Hillcrest utility works", "completed", -5, 680000),
    ]):
        start = today + timedelta(days=offset)
        job = add(Job, customer_id=customers[index % 3].id, number=f"FD-{1041 + index}", title=title,
                  site=["Muskoka, ON", "Barrie, ON", "Orillia, ON"][index % 3] + " · Fictional site",
                  service="Site services", requested_start=start, requested_end=start + timedelta(days=1), status=status, version=1)
        quote = add(Quote, job_id=job.id, revision=1, state="draft" if status == "draft" else "approved", total_cents=cents)
        add(QuoteLine, quote_id=quote.id, position=0, description="Illustrative site services package",
            quantity="1", unit_price=f"{cents / 100:.2f}", total_cents=cents)
        if status in {"scheduled", "in_progress", "completed"}:
            add(Assignment, job_id=job.id, crew_id=crews[index % 3].id, equipment_id=equipment[index % 3].id,
                start_date=start, end_date=start + timedelta(days=1))
        add(ActivityEvent, job_id=job.id, kind="sample", text=f"Sample project loaded · {title}")
