"""
Template-based prototype generator — zero API calls.
Produces the same 5-screen wireframe HTML as prototype_agent.py using structured
plan data. Drop-in replacement for prototype_agent.generate_prototype.
"""
from datetime import date
from agents.rules.lookup import normalize_domain

# ── Domain colour schemes ────────────────────────────────────────────────────

_COLORS = {
    "ecommerce":   ("#f97316", "#ea580c"),   # orange
    "edtech":      ("#6366f1", "#4f46e5"),   # indigo
    "fintech":     ("#0ea5e9", "#0284c7"),   # sky
    "healthcare":  ("#10b981", "#059669"),   # emerald
    "erp":         ("#64748b", "#475569"),   # slate
    "social":      ("#ec4899", "#db2777"),   # pink
    "productivity":("#8b5cf6", "#7c3aed"),   # violet
    "saas":        ("#4f46e5", "#4338ca"),   # indigo
}

# ── Domain sample data ────────────────────────────────────────────────────────

_STATS: dict[str, list[tuple]] = {
    "ecommerce":   [("💰", "$24,830", "Revenue today", "+12%"), ("📦", "143", "Orders placed", "+8%"), ("👥", "1,204", "Active users", "+5%"), ("📈", "3.2%", "Conversion rate", "+0.4%")],
    "edtech":      [("🎓", "3,812", "Enrolled students", "+9%"), ("📚", "47", "Courses published", "+3"), ("✅", "68%", "Completion rate", "+2%"), ("💵", "$18,450", "Monthly revenue", "+15%")],
    "fintech":     [("💳", "$1.2M", "Total balance", "+4%"), ("🔄", "892", "Transactions today", "+11%"), ("🏦", "5,341", "Active accounts", "+7%"), ("⏳", "23", "Pending reviews", "-5")],
    "healthcare":  [("🏥", "84", "Patients today", "+6"), ("📅", "127", "Appointments", "+3%"), ("⏱", "12 min", "Avg wait time", "-2 min"), ("👩‍⚕️", "34", "Staff on duty", "—")],
    "social":      [("👤", "42,891", "Active users", "+18%"), ("📝", "8,340", "Posts today", "+23%"), ("❤️", "124K", "Reactions", "+31%"), ("💬", "9,821", "Comments", "+17%")],
    "productivity":[("✅", "1,247", "Tasks completed", "+14%"), ("📂", "84", "Active projects", "+2"), ("👥", "312", "Team members", "+8"), ("⚡", "94%", "On-time rate", "+3%")],
    "erp":         [("📦", "2,341", "Inventory items", "+42"), ("🧾", "$387K", "Open invoices", "-8%"), ("👩‍💼", "89", "Active employees", "+2"), ("🔄", "34", "Pending orders", "+5")],
    "saas":        [("👤", "4,201", "Active users", "+12%"), ("💰", "$83,200", "MRR", "+9%"), ("🔑", "342", "API calls/hr", "+5%"), ("📊", "97.8%", "Uptime", "—")],
}

_ACTIVITY: dict[str, list[tuple]] = {
    "ecommerce":   [("🛒", "Order #4821 placed", "Emma Wilson", "2 min ago"), ("✅", "Order #4820 shipped", "James Carter", "8 min ago"), ("💳", "Payment received — $249", "Priya Singh", "14 min ago"), ("🔄", "Return request #812", "Tom Blake", "31 min ago"), ("⭐", "5-star review left", "Maria Lopez", "45 min ago"), ("📦", "New product listed", "Admin", "1 hr ago")],
    "edtech":      [("🎓", "Course completed: Python 101", "Alex Kim", "3 min ago"), ("📝", "Quiz submitted — 87%", "Sara Patel", "11 min ago"), ("🆕", "New enrollment: Data Science", "Raj Mehta", "22 min ago"), ("💬", "Forum reply posted", "Lisa Chen", "38 min ago"), ("🏅", "Certificate issued", "Mark Davis", "52 min ago"), ("📚", "Lesson published", "Instructor", "1 hr ago")],
    "fintech":     [("💸", "Transfer — $1,200", "Alice Turner", "1 min ago"), ("✅", "KYC approved", "Ben Foster", "9 min ago"), ("🔔", "Low balance alert sent", "System", "17 min ago"), ("💳", "Card activated", "Chloe Park", "28 min ago"), ("📥", "Deposit — $5,000", "Dan Hughes", "41 min ago"), ("🔐", "Password changed", "Eve Walsh", "1 hr ago")],
    "healthcare":  [("📅", "Appointment booked — Dr. Lee", "John Smith", "4 min ago"), ("📋", "Lab results uploaded", "Nurse Chen", "13 min ago"), ("💊", "Prescription sent", "Dr. Patel", "26 min ago"), ("🚑", "Emergency note added", "Dr. Ross", "34 min ago"), ("✅", "Discharge completed", "Ward 3", "49 min ago"), ("📞", "Telemedicine call ended", "Dr. Kim", "1 hr ago")],
    "social":      [("❤️", "Post liked", "User @maya_r", "just now"), ("💬", "Comment added", "User @devraj", "2 min ago"), ("👥", "New follower", "User @lena_k", "5 min ago"), ("🔁", "Post reshared", "User @tomwill", "12 min ago"), ("🆕", "New post published", "User @clara_b", "19 min ago"), ("🚩", "Report submitted", "Moderator", "33 min ago")],
    "productivity":[("✅", "Task closed: Deploy v2.1", "Alice Wong", "just now"), ("📝", "Comment on #PRJ-812", "Dev Team", "4 min ago"), ("🆕", "Sprint started: Week 22", "PM Bot", "12 min ago"), ("🔗", "PR merged — feature/auth", "Jake Liu", "23 min ago"), ("📅", "Deadline updated", "Sara M.", "37 min ago"), ("📂", "Project archived", "Admin", "1 hr ago")],
    "erp":         [("📦", "PO #8821 received", "Warehouse", "3 min ago"), ("🧾", "Invoice #INV-442 sent", "Finance", "10 min ago"), ("👤", "New hire onboarded", "HR", "22 min ago"), ("🔄", "Stock reorder triggered", "System", "35 min ago"), ("✅", "Payroll processed", "Finance", "50 min ago"), ("📊", "Monthly report ready", "Reports", "1 hr ago")],
    "saas":        [("🆕", "New signup: Acme Corp", "Growth", "1 min ago"), ("⬆️", "Plan upgraded: Pro → Enterprise", "BillingBot", "8 min ago"), ("🔑", "API key generated", "Dev: jsmith", "15 min ago"), ("📧", "Onboarding email sent", "System", "28 min ago"), ("🐛", "Bug report #412 opened", "Support", "42 min ago"), ("✅", "Subscription renewed", "Stripe", "1 hr ago")],
}

_TABLE: dict[str, tuple[list[str], list[list[str]]]] = {
    "ecommerce": (
        ["Order ID", "Customer", "Items", "Total", "Status", "Date"],
        [["#4821","Emma Wilson","3","$142.00","✅ Shipped","May 25"],["#4820","James Carter","1","$89.00","✅ Shipped","May 25"],["#4819","Priya Singh","5","$310.00","🕐 Processing","May 24"],["#4818","Tom Blake","2","$67.50","🔄 Return","May 24"],["#4817","Maria Lopez","4","$224.00","✅ Delivered","May 23"],["#4816","Sam Reed","1","$45.00","✅ Delivered","May 23"],["#4815","Nina Roy","7","$481.00","✅ Delivered","May 22"],["#4814","Chris Hall","2","$130.00","❌ Cancelled","May 22"]],
    ),
    "edtech": (
        ["Student", "Course", "Progress", "Score", "Status", "Enrolled"],
        [["Alex Kim","Python 101","100%","92","✅ Complete","Mar 10"],["Sara Patel","Data Science","74%","87","🔵 Active","Apr 2"],["Raj Mehta","Web Dev Bootcamp","12%","—","🆕 New","May 20"],["Lisa Chen","UX Design","88%","94","🔵 Active","Feb 14"],["Mark Davis","ML Fundamentals","100%","78","✅ Complete","Jan 8"],["Jess Kim","React Mastery","45%","81","🔵 Active","Apr 19"],["Omar Ali","SQL Basics","60%","88","🔵 Active","Mar 28"],["Tara Singh","Cloud Arch.","30%","—","🔵 Active","May 5"]],
    ),
    "fintech": (
        ["Tx ID", "Account", "Type", "Amount", "Status", "Date"],
        [["TXN-9921","Alice Turner","Transfer","$1,200","✅ Complete","May 25"],["TXN-9920","Ben Foster","Deposit","$5,000","✅ Complete","May 25"],["TXN-9919","Chloe Park","Withdrawal","$300","🕐 Pending","May 24"],["TXN-9918","Dan Hughes","Transfer","$750","✅ Complete","May 24"],["TXN-9917","Eve Walsh","Deposit","$2,500","✅ Complete","May 23"],["TXN-9916","Frank Kim","Payment","$120","❌ Failed","May 23"],["TXN-9915","Grace Li","Transfer","$4,000","✅ Complete","May 22"],["TXN-9914","Hank Moss","Withdrawal","$600","🕐 Pending","May 22"]],
    ),
    "healthcare": (
        ["Patient", "Provider", "Type", "Date/Time", "Status", "Room"],
        [["John Smith","Dr. Lee","Check-up","May 25 09:00","✅ Confirmed","A12"],["Sara Jones","Dr. Patel","Follow-up","May 25 10:30","✅ Confirmed","B4"],["Mike Brown","Dr. Ross","Lab Review","May 25 11:00","🕐 Waiting","C7"],["Lily Kim","Dr. Chen","Telemedicine","May 25 13:00","📞 Online","—"],["Tom Reed","Dr. Lee","Emergency","May 25 14:30","🔴 Urgent","ER-2"],["Amy Park","Dr. Patel","New Patient","May 26 09:00","✅ Confirmed","A8"],["Carlos M.","Dr. Kim","X-Ray Review","May 26 10:00","🕐 Pending","D3"],["Emma White","Dr. Ross","Discharge","May 25 15:00","✅ Confirmed","C7"]],
    ),
    "social": (
        ["User", "Post", "Likes", "Comments", "Shares", "Date"],
        [["@maya_r","Summer vibes 🌊","1.2K","84","201","May 25"],["@devraj","Just launched v2!","887","62","143","May 25"],["@lena_k","Morning routine 🧘","641","31","88","May 24"],["@tomwill","Thread: AI tools","2.4K","198","512","May 24"],["@clara_b","City walk 📷","430","19","57","May 23"],["@alexd","Hot take: tabs > spaces","3.1K","341","720","May 23"],["@priya","New recipe 🍜","521","44","112","May 22"],["@samir","Weekend project 🛠","319","28","64","May 22"]],
    ),
    "productivity": (
        ["Task", "Project", "Assignee", "Priority", "Due", "Status"],
        [["Design login screen","Web App v2","Alice W.","🔴 High","May 26","🔵 In Progress"],["Write API docs","Backend","Jake L.","🟡 Med","May 28","📋 Todo"],["Fix auth bug #812","Backend","Sara M.","🔴 High","May 25","🔵 In Progress"],["QA — checkout flow","Web App v2","QA Team","🟡 Med","May 30","📋 Todo"],["Deploy staging env","DevOps","Ops Bot","🔴 High","May 25","✅ Done"],["User interviews x5","Research","PM","🟢 Low","Jun 1","🔵 In Progress"],["Update README","Backend","Jake L.","🟢 Low","Jun 3","📋 Todo"],["Sprint retro prep","All","PM","🟡 Med","May 27","📋 Todo"]],
    ),
    "erp": (
        ["Item", "Category", "Stock", "Reorder At", "Supplier", "Status"],
        [["Widget A","Hardware","1,240","200","Acme Co.","✅ OK"],["Widget B","Hardware","87","150","Acme Co.","⚠️ Low"],["Component X","Electronics","432","100","TechParts","✅ OK"],["Raw Steel","Materials","2,100","500","MetalCorp","✅ OK"],["Packaging Box","Supplies","340","400","PackCo","⚠️ Low"],["Circuit Board","Electronics","18","50","TechParts","🔴 Critical"],["Label Set","Supplies","890","200","PackCo","✅ OK"],["Bolt M6","Hardware","5,200","1000","Acme Co.","✅ OK"]],
    ),
    "saas": (
        ["Account", "Plan", "Users", "MRR", "Status", "Since"],
        [["Acme Corp","Enterprise","124","$2,400","✅ Active","Jan 2024"],["Beta Inc.","Pro","18","$299","✅ Active","Mar 2024"],["Gamma LLC","Starter","5","$49","✅ Active","Apr 2024"],["Delta Co.","Enterprise","88","$1,800","⚠️ Past Due","Feb 2024"],["Epsilon Ltd","Pro","31","$299","✅ Active","Nov 2023"],["Zeta Ltd","Starter","3","$49","🕐 Trial","May 2024"],["Eta Corp","Enterprise","201","$4,200","✅ Active","Aug 2023"],["Theta Inc","Pro","12","$299","❌ Churned","Dec 2023"]],
    ),
}

_DETAIL_FIELDS: dict[str, list[tuple[str, str]]] = {
    "ecommerce":   [("Order ID","#4821"),("Customer","Emma Wilson"),("Email","emma@example.com"),("Items","3 items — see breakdown"),("Subtotal","$128.00"),("Shipping","$14.00"),("Total","$142.00"),("Status","Shipped"),("Shipping address","14 Oak Lane, Austin TX 78701"),("Carrier","FedEx — tracking #794821")],
    "edtech":      [("Student","Alex Kim"),("Email","alex.kim@example.com"),("Course","Python 101"),("Enrolled","Mar 10, 2024"),("Progress","100% complete"),("Last active","May 24, 2024"),("Quiz avg","92 / 100"),("Certificate","Issued May 25, 2024"),("Cohort","Spring 2024"),("Instructor","Dr. Sarah Lee")],
    "fintech":     [("Transaction","TXN-9921"),("Account","Alice Turner — ACC-0042"),("Type","Outgoing Transfer"),("Amount","$1,200.00"),("Status","Completed"),("Date","May 25, 2024 09:14"),("Recipient","Ben Foster — ACC-0107"),("Reference","Rent — May 2024"),("Auth method","2FA verified"),("IP address","203.0.113.42")],
    "healthcare":  [("Patient","John Smith"),("DOB","1985-06-12 (Age 38)"),("Provider","Dr. Lee"),("Appointment","May 25, 09:00 — Room A12"),("Type","Annual check-up"),("Insurance","BlueCross #BC-88421"),("Allergies","Penicillin"),("Last visit","Nov 12, 2023"),("BP","118/76 mmHg"),("Notes","Follow up on cholesterol levels")],
    "social":      [("User","@maya_r"),("Full name","Maya Rodriguez"),("Joined","Jan 15, 2023"),("Followers","8,421"),("Following","312"),("Posts","1,204"),("Account type","Creator"),("Bio","Surf • Travel • Coffee ☕"),("Location","San Diego, CA"),("Last active","May 25, 2024")],
    "productivity":[("Task","Fix auth bug #812"),("Project","Backend"),("Assignee","Sara M."),("Reporter","Jake L."),("Priority","High"),("Status","In Progress"),("Created","May 22, 2024"),("Due","May 25, 2024"),("Sprint","Sprint 14"),("Description","JWT tokens not refreshing on mobile browsers — see Slack thread #eng-bugs")],
    "erp":         [("Item","Widget B"),("SKU","WGT-B-0042"),("Category","Hardware"),("Stock","87 units"),("Reorder at","150 units"),("Supplier","Acme Co."),("Lead time","7 business days"),("Unit cost","$4.20"),("Last restocked","May 10, 2024"),("Warehouse","Shelf B-14")],
    "saas":        [("Account","Acme Corp"),("Plan","Enterprise"),("Users","124 seats"),("MRR","$2,400"),("Status","Active"),("Billing","Monthly — Visa ****4821"),("Next invoice","Jun 1, 2024"),("CSM","Jess Kim"),("Contract end","Dec 31, 2024"),("Last login","May 25, 2024 (CEO)")],
}

_FORM_FIELDS: dict[str, list[tuple[str, str, str]]] = {
    "ecommerce":   [("Product name","text","Blue Running Shoes"),("SKU","text","SKU-9821"),("Price","number","89.99"),("Category","select","Footwear"),("Stock qty","number","250"),("Description","textarea","Premium running shoes..."),("Weight (kg)","number","0.8"),("Status","select","Published")],
    "edtech":      [("Course title","text","Advanced Python"),("Instructor","select","Dr. Sarah Lee"),("Category","select","Programming"),("Price ($)","number","49"),("Duration (hrs)","number","12"),("Description","textarea","A hands-on course..."),("Difficulty","select","Intermediate"),("Status","select","Draft")],
    "fintech":     [("Account holder","text","Alice Turner"),("Account type","select","Savings"),("Currency","select","USD"),("Initial balance","number","5000"),("Interest rate (%)","number","2.5"),("Credit limit","number","10000"),("KYC status","select","Verified"),("Notes","textarea","VIP customer")],
    "healthcare":  [("Patient name","text","John Smith"),("Date of birth","date","1985-06-12"),("Gender","select","Male"),("Phone","text","+1 512 555 0142"),("Insurance ID","text","BC-88421"),("Provider","select","Dr. Lee"),("Appointment date","date","2024-06-01"),("Notes","textarea","Follow up required")],
    "social":      [("Display name","text","Maya Rodriguez"),("Username","text","@maya_r"),("Bio","textarea","Surf • Travel • Coffee"),("Website","text","maya.blog"),("Location","text","San Diego, CA"),("Account type","select","Creator"),("Verified","select","No"),("Status","select","Active")],
    "productivity":[("Task title","text","Fix auth bug #812"),("Project","select","Backend"),("Assignee","select","Sara M."),("Priority","select","High"),("Due date","date","2024-05-25"),("Sprint","select","Sprint 14"),("Labels","text","bug, backend, urgent"),("Description","textarea","JWT tokens not refreshing...")],
    "erp":         [("Item name","text","Widget B"),("SKU","text","WGT-B-0042"),("Category","select","Hardware"),("Unit cost ($)","number","4.20"),("Stock qty","number","87"),("Reorder threshold","number","150"),("Supplier","select","Acme Co."),("Warehouse location","text","Shelf B-14")],
    "saas":        [("Account name","text","Acme Corp"),("Plan","select","Enterprise"),("Seats","number","124"),("MRR ($)","number","2400"),("CSM","select","Jess Kim"),("Contract end","date","2024-12-31"),("Billing cycle","select","Monthly"),("Notes","textarea","Expansion discussion in Q3")],
}

_SCREEN_NAMES: dict[str, list[str]] = {
    "ecommerce":   ["Dashboard","Orders","Order Detail","New Product","Settings"],
    "edtech":      ["Dashboard","Students","Student Detail","New Course","Settings"],
    "fintech":     ["Dashboard","Transactions","Transaction Detail","New Account","Settings"],
    "healthcare":  ["Dashboard","Appointments","Patient Detail","New Appointment","Settings"],
    "social":      ["Dashboard","Posts","User Detail","New Post","Settings"],
    "productivity":["Dashboard","Tasks","Task Detail","New Task","Settings"],
    "erp":         ["Dashboard","Inventory","Item Detail","New Item","Settings"],
    "saas":        ["Dashboard","Accounts","Account Detail","New Account","Settings"],
}


# ── HTML helpers ─────────────────────────────────────────────────────────────

def _h(t) -> str:
    return str(t).replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def _card(icon: str, value: str, label: str, trend: str, c1: str) -> str:
    trend_color = "#10b981" if trend.startswith("+") else "#ef4444" if trend.startswith("-") else "#6b7280"
    return f"""
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:1rem;">
      <div style="font-size:1.5rem;margin-bottom:0.5rem;">{icon}</div>
      <div style="font-size:1.5rem;font-weight:700;color:{c1};">{_h(value)}</div>
      <div style="font-size:0.78rem;color:#64748b;margin-top:0.1rem;">{_h(label)}</div>
      <div style="font-size:0.72rem;font-weight:600;color:{trend_color};margin-top:0.25rem;">{_h(trend)} vs yesterday</div>
    </div>"""

def _screen_wrap(n: int, name: str, desc: str, url: str, color: str, body: str) -> str:
    return f"""
<div class="sw">
  <div class="sl" style="background:{color}">
    <span>Screen {n} — {_h(name)}</span>
    <span style="font-weight:400;font-size:0.82rem;opacity:0.85">{_h(desc)}</span>
  </div>
  <div class="bc">
    <div class="bd">
      <span class="bdt" style="background:#ef4444"></span>
      <span class="bdt" style="background:#f59e0b"></span>
      <span class="bdt" style="background:#22c55e"></span>
    </div>
    <div class="bu">{_h(url)}</div>
  </div>
  <div class="sb p-6">{body}</div>
</div>"""


# ── Screen builders ───────────────────────────────────────────────────────────

def _screen1_dashboard(domain: str, app_name: str, color: str) -> str:
    stats = _STATS.get(domain, _STATS["saas"])
    cards = "".join(_card(i, v, l, t, color) for i, v, l, t in stats)

    activity = _ACTIVITY.get(domain, _ACTIVITY["saas"])
    rows = "".join(
        f'<div style="display:flex;align-items:center;gap:0.75rem;padding:0.6rem 0;border-bottom:1px solid #f1f5f9;">'
        f'<span style="font-size:1.1rem;width:24px;text-align:center;">{icon}</span>'
        f'<div style="flex:1;min-width:0;"><div style="font-size:0.85rem;color:#1e293b;font-weight:500;">{_h(desc)}</div>'
        f'<div style="font-size:0.75rem;color:#94a3b8;">{_h(user)}</div></div>'
        f'<div style="font-size:0.72rem;color:#94a3b8;white-space:nowrap;">{_h(ts)}</div></div>'
        for icon, desc, user, ts in activity
    )

    # CSS bar chart
    bar_data = [("Mon", 45), ("Tue", 62), ("Wed", 58), ("Thu", 80), ("Fri", 73), ("Sat", 91), ("Sun", 55)]
    max_v = max(v for _, v in bar_data)
    bars = "".join(
        f'<div style="display:flex;flex-direction:column;align-items:center;gap:0.3rem;flex:1;">'
        f'<div style="width:28px;height:{int(v/max_v*80)}px;background:{color};border-radius:4px 4px 0 0;opacity:0.85;"></div>'
        f'<div style="font-size:0.65rem;color:#94a3b8;">{d}</div></div>'
        for d, v in bar_data
    )

    body = f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem;">
      <div>
        <h2 style="font-size:1.1rem;font-weight:700;color:#1e293b;margin:0;">Dashboard</h2>
        <p style="font-size:0.8rem;color:#94a3b8;margin:0.1rem 0 0;">Welcome back — here's what's happening today</p>
      </div>
      <button style="background:{color};color:white;border:none;border-radius:8px;padding:0.5rem 1rem;font-size:0.8rem;font-weight:600;cursor:pointer;">+ New</button>
    </div>
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:0.75rem;margin-bottom:1.5rem;">{cards}</div>
    <div style="display:grid;grid-template-columns:2fr 1fr;gap:1rem;">
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:1rem;">
        <div style="font-size:0.82rem;font-weight:600;color:#374151;margin-bottom:0.75rem;">Weekly Activity</div>
        <div style="display:flex;align-items:flex-end;height:100px;gap:4px;padding:0 0.5rem;">{bars}</div>
      </div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:1rem;">
        <div style="font-size:0.82rem;font-weight:600;color:#374151;margin-bottom:0.5rem;">Recent Activity</div>
        {rows}
      </div>
    </div>"""
    screens = _SCREEN_NAMES.get(domain, _SCREEN_NAMES["saas"])
    return _screen_wrap(1, screens[0], f"Overview and key metrics", f"{app_name.lower().replace(' ','-')}.app/dashboard", color, body)


def _screen2_list(domain: str, app_name: str, color: str) -> str:
    cols, rows = _TABLE.get(domain, _TABLE["saas"])
    header_cells = "".join(f'<th style="background:#f1f5f9;color:#475569;padding:8px 12px;text-align:left;font-size:0.72rem;text-transform:uppercase;letter-spacing:0.05em;white-space:nowrap;">{_h(c)} ↕</th>' for c in cols)
    data_rows = ""
    for row in rows:
        cells = "".join(f'<td style="padding:8px 12px;font-size:0.82rem;color:#334155;border-bottom:1px solid #f1f5f9;white-space:nowrap;">{_h(v)}</td>' for v in row)
        cells += f'<td style="padding:8px 12px;border-bottom:1px solid #f1f5f9;"><button style="font-size:0.72rem;color:{color};border:1px solid {color};background:white;border-radius:5px;padding:2px 8px;cursor:pointer;">View</button></td>'
        data_rows += f"<tr>{cells}</tr>"

    filter_chips = "".join(
        f'<span style="display:inline-block;padding:4px 12px;border-radius:9999px;font-size:0.75rem;font-weight:600;cursor:pointer;'
        + (f'background:{color};color:white;">' if i == 0 else 'background:#f1f5f9;color:#475569;border:1px solid #e2e8f0;">')
        + f'{lbl}</span>'
        for i, lbl in enumerate(["All", "Active", "Pending", "Archived"])
    )

    body = f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem;">
      <h2 style="font-size:1.1rem;font-weight:700;color:#1e293b;margin:0;">{_h(_SCREEN_NAMES.get(domain, _SCREEN_NAMES['saas'])[1])}</h2>
      <button style="background:{color};color:white;border:none;border-radius:8px;padding:0.5rem 1rem;font-size:0.8rem;font-weight:600;cursor:pointer;">+ Add New</button>
    </div>
    <div style="display:flex;align-items:center;gap:0.75rem;margin-bottom:1rem;">
      <input placeholder="🔍  Search…" style="flex:1;max-width:320px;border:1px solid #e2e8f0;border-radius:8px;padding:0.4rem 0.75rem;font-size:0.82rem;color:#374151;" />
      <div style="display:flex;gap:0.5rem;">{filter_chips}</div>
    </div>
    <div style="overflow-x:auto;">
      <table style="width:100%;border-collapse:collapse;">
        <thead><tr>{header_cells}<th style="background:#f1f5f9;padding:8px 12px;"></th></tr></thead>
        <tbody>{data_rows}</tbody>
      </table>
    </div>
    <div style="display:flex;justify-content:space-between;align-items:center;margin-top:1rem;font-size:0.78rem;color:#94a3b8;">
      <span>Showing 8 of 143 records</span>
      <div style="display:flex;gap:0.5rem;">
        <button style="border:1px solid #e2e8f0;border-radius:6px;padding:4px 10px;cursor:pointer;">← Prev</button>
        <button style="border:1px solid {color};background:{color};color:white;border-radius:6px;padding:4px 10px;cursor:pointer;">1</button>
        <button style="border:1px solid #e2e8f0;border-radius:6px;padding:4px 10px;cursor:pointer;">2</button>
        <button style="border:1px solid #e2e8f0;border-radius:6px;padding:4px 10px;cursor:pointer;">Next →</button>
      </div>
    </div>"""
    screens = _SCREEN_NAMES.get(domain, _SCREEN_NAMES["saas"])
    return _screen_wrap(2, screens[1], "Search, filter, and manage records", f"{app_name.lower().replace(' ','-')}.app/{screens[1].lower()}", color, body)


def _screen3_detail(domain: str, app_name: str, color: str) -> str:
    fields = _DETAIL_FIELDS.get(domain, _DETAIL_FIELDS["saas"])
    field_cells = "".join(
        f'<div style="padding:0.5rem 0;border-bottom:1px solid #f1f5f9;">'
        f'<div style="font-size:0.72rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;">{_h(k)}</div>'
        f'<div style="font-size:0.88rem;color:#1e293b;font-weight:500;margin-top:0.15rem;">{_h(v)}</div>'
        f'</div>'
        for k, v in fields
    )
    half = len(fields) // 2
    left = "".join(
        f'<div style="padding:0.5rem 0;border-bottom:1px solid #f1f5f9;">'
        f'<div style="font-size:0.72rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;">{_h(fields[i][0])}</div>'
        f'<div style="font-size:0.88rem;color:#1e293b;font-weight:500;margin-top:0.15rem;">{_h(fields[i][1])}</div>'
        f'</div>'
        for i in range(half)
    )
    right = "".join(
        f'<div style="padding:0.5rem 0;border-bottom:1px solid #f1f5f9;">'
        f'<div style="font-size:0.72rem;color:#94a3b8;text-transform:uppercase;letter-spacing:0.05em;">{_h(fields[i][0])}</div>'
        f'<div style="font-size:0.88rem;color:#1e293b;font-weight:500;margin-top:0.15rem;">{_h(fields[i][1])}</div>'
        f'</div>'
        for i in range(half, len(fields))
    )

    screens = _SCREEN_NAMES.get(domain, _SCREEN_NAMES["saas"])
    title = fields[0][1] if fields else "Record"
    body = f"""
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.25rem;flex-wrap:wrap;">
      <button style="font-size:0.78rem;color:{color};border:none;background:none;cursor:pointer;">← Back to {_h(screens[1])}</button>
      <div style="flex:1;min-width:0;">
        <h2 style="font-size:1.1rem;font-weight:700;color:#1e293b;margin:0;">{_h(title)}</h2>
      </div>
      <span style="background:#dcfce7;color:#166534;padding:3px 10px;border-radius:9999px;font-size:0.75rem;font-weight:600;">Active</span>
      <button style="border:1px solid #e2e8f0;border-radius:8px;padding:6px 14px;font-size:0.8rem;cursor:pointer;">Edit</button>
      <button style="border:1px solid #e2e8f0;border-radius:8px;padding:6px 14px;font-size:0.8rem;cursor:pointer;">Archive</button>
      <button style="background:{color};color:white;border:none;border-radius:8px;padding:6px 14px;font-size:0.8rem;cursor:pointer;">Share</button>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0 2rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:1rem;margin-bottom:1rem;">
      <div>{left}</div><div>{right}</div>
    </div>
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:1rem;">
      <div style="font-size:0.82rem;font-weight:600;color:#374151;margin-bottom:0.75rem;">Related Items</div>
      {"".join(f'<div style="display:flex;justify-content:space-between;padding:0.5rem 0;border-bottom:1px solid #f1f5f9;font-size:0.82rem;"><span style="color:#334155;">Item #{i+1}</span><span style="color:#94a3b8;">May {20+i}, 2024</span><span style="color:{color};cursor:pointer;">View →</span></div>' for i in range(4))}
    </div>"""
    return _screen_wrap(3, screens[2], "Full record detail and related items", f"{app_name.lower().replace(' ','-')}.app/{screens[1].lower()}/detail", color, body)


def _screen4_form(domain: str, app_name: str, color: str) -> str:
    fields = _FORM_FIELDS.get(domain, _FORM_FIELDS["saas"])
    screens = _SCREEN_NAMES.get(domain, _SCREEN_NAMES["saas"])

    form_inputs = []
    for label, ftype, placeholder in fields:
        required = "* " if ftype != "textarea" else ""
        if ftype == "select":
            inp = f'<select style="width:100%;border:1px solid #e2e8f0;border-radius:6px;padding:0.4rem 0.6rem;font-size:0.82rem;color:#374151;"><option>{_h(placeholder)}</option></select>'
        elif ftype == "textarea":
            inp = f'<textarea rows="3" placeholder="{_h(placeholder)}" style="width:100%;border:1px solid #e2e8f0;border-radius:6px;padding:0.4rem 0.6rem;font-size:0.82rem;color:#374151;resize:none;"></textarea>'
        else:
            inp = f'<input type="{ftype}" value="{_h(placeholder)}" style="width:100%;border:1px solid #e2e8f0;border-radius:6px;padding:0.4rem 0.6rem;font-size:0.82rem;color:#374151;" />'
        form_inputs.append(
            f'<div><label style="display:block;font-size:0.78rem;font-weight:600;color:#374151;margin-bottom:0.25rem;">{required}{_h(label)}</label>{inp}</div>'
        )

    half = len(form_inputs) // 2
    left_inputs  = "".join(form_inputs[:half])
    right_inputs = "".join(form_inputs[half:])

    body = f"""
    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:1.25rem;">
      <h2 style="font-size:1.1rem;font-weight:700;color:#1e293b;margin:0;">{screens[3]}</h2>
      <div style="display:flex;gap:0.5rem;">
        <button style="border:1px solid #e2e8f0;border-radius:8px;padding:6px 16px;font-size:0.8rem;cursor:pointer;">Cancel</button>
        <button style="background:{color};color:white;border:none;border-radius:8px;padding:6px 16px;font-size:0.8rem;font-weight:600;cursor:pointer;">Save</button>
      </div>
    </div>
    <div style="font-size:0.72rem;color:#94a3b8;margin-bottom:1rem;">* Required fields</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem 1.5rem;margin-bottom:1.5rem;">
      <div style="display:flex;flex-direction:column;gap:0.75rem;">{left_inputs}</div>
      <div style="display:flex;flex-direction:column;gap:0.75rem;">{right_inputs}</div>
    </div>
    <button style="width:100%;background:{color};color:white;border:none;border-radius:8px;padding:0.75rem;font-size:0.9rem;font-weight:600;cursor:pointer;">Save {screens[3].replace('New ','')}</button>"""
    return _screen_wrap(4, screens[3], "Create or edit a record", f"{app_name.lower().replace(' ','-')}.app/{screens[1].lower()}/new", color, body)


def _screen5_settings(domain: str, app_name: str, color: str) -> str:
    toggles = [
        ("Email notifications for new activity", True),
        ("Weekly digest summary", True),
        ("In-app push notifications", False),
        ("SMS alerts for critical events", False),
        ("Marketing and product updates", True),
        ("Security alerts (logins, password changes)", True),
    ]
    toggle_rows = "".join(
        f'<div style="display:flex;align-items:center;justify-content:space-between;padding:0.65rem 0;border-bottom:1px solid #f1f5f9;">'
        f'<span style="font-size:0.85rem;color:#334155;">{_h(label)}</span>'
        f'<div style="width:36px;height:20px;border-radius:9999px;background:{""+color+"" if on else "#e2e8f0"};cursor:pointer;position:relative;">'
        f'<div style="width:16px;height:16px;border-radius:50%;background:white;position:absolute;top:2px;{"right:2px" if on else "left:2px"};"></div>'
        f'</div></div>'
        for label, on in toggles
    )

    body = f"""
    <div style="margin-bottom:1.25rem;">
      <h2 style="font-size:1.1rem;font-weight:700;color:#1e293b;margin:0 0 1rem;">Settings</h2>
      <div style="display:flex;gap:0;border-bottom:2px solid #e2e8f0;">
        {"".join(f'<button style="padding:0.5rem 1rem;font-size:0.82rem;font-weight:600;border:none;background:none;cursor:pointer;{"color:"+color+";border-bottom:2px solid "+color+";margin-bottom:-2px;" if i==0 else "color:#94a3b8;"}">{tab}</button>' for i, tab in enumerate(["Account","Notifications","Preferences"]))}
      </div>
    </div>
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1.5rem;padding:1rem;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;">
      <div style="width:56px;height:56px;border-radius:50%;background:{color};color:white;display:flex;align-items:center;justify-content:center;font-size:1.2rem;font-weight:700;">AK</div>
      <div style="flex:1;">
        <div style="font-size:1rem;font-weight:700;color:#1e293b;">Alex Kim</div>
        <div style="font-size:0.82rem;color:#94a3b8;">alex.kim@example.com · Admin</div>
      </div>
      <button style="border:1px solid {color};color:{color};background:white;border-radius:8px;padding:6px 14px;font-size:0.8rem;cursor:pointer;">Edit Profile</button>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:0.75rem 1.5rem;margin-bottom:1.5rem;">
      {"".join(f'<div><label style="display:block;font-size:0.78rem;font-weight:600;color:#374151;margin-bottom:0.25rem;">{_h(lbl)}</label><input value="{_h(val)}" style="width:100%;border:1px solid #e2e8f0;border-radius:6px;padding:0.4rem 0.6rem;font-size:0.82rem;color:#374151;" /></div>' for lbl, val in [("First name","Alex"),("Last name","Kim"),("Email","alex.kim@example.com"),("Phone","+1 415 555 0142")])}
    </div>
    <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:1rem;margin-bottom:1.25rem;">
      <div style="font-size:0.82rem;font-weight:600;color:#374151;margin-bottom:0.5rem;">Notifications</div>
      {toggle_rows}
    </div>
    <button style="background:{color};color:white;border:none;border-radius:8px;padding:0.65rem 1.5rem;font-size:0.85rem;font-weight:600;cursor:pointer;">Save Changes</button>"""
    return _screen_wrap(5, "Settings", "Account info and notification preferences", f"{app_name.lower().replace(' ','-')}.app/settings", color, body)


# ── Public API ────────────────────────────────────────────────────────────────

async def generate_prototype(
    requirements: dict,
    architecture: dict,
    tech_stack: dict,
) -> str:
    """
    Generate a 5-screen wireframe HTML document from structured plan data.
    No API calls — pure template rendering. Drop-in for prototype_agent.generate_prototype.
    """
    domain_raw = requirements.get("domain", "saas")
    domain = normalize_domain(domain_raw)
    app_name = requirements.get("project_name") or requirements.get("name") or "MyApp"
    today = date.today().strftime("%B %d, %Y")

    c1, c2 = _COLORS.get(domain, _COLORS["saas"])
    screens = _SCREEN_NAMES.get(domain, _SCREEN_NAMES["saas"])

    head = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{_h(app_name)} — UI Wireframe</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    body {{ background: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 0; }}
    .sw {{ max-width: 960px; margin: 0 auto 3rem; padding: 0 1rem; }}
    .sl {{ color: white; padding: 0.75rem 1.25rem; border-radius: 12px 12px 0 0; font-weight: 700; font-size: 0.95rem; display: flex; justify-content: space-between; align-items: center; }}
    .bc {{ background: #e2e8f0; padding: 0.4rem 0.75rem; display: flex; align-items: center; gap: 0.5rem; font-size: 0.72rem; color: #64748b; border-left: 1px solid #cbd5e1; border-right: 1px solid #cbd5e1; }}
    .bd {{ display: flex; gap: 4px; flex-shrink: 0; }}
    .bdt {{ width: 10px; height: 10px; border-radius: 50%; display: inline-block; }}
    .bu {{ background: white; border-radius: 4px; padding: 2px 10px; flex: 1; max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    .sb {{ background: white; border: 1px solid #cbd5e1; border-top: none; border-radius: 0 0 12px 12px; overflow: hidden; min-height: 480px; }}
  </style>
</head>
<body>

<div style="background:linear-gradient(135deg,{c1},{c2});color:white;text-align:center;padding:3rem 1rem 2.5rem;margin-bottom:2rem;">
  <div style="font-size:2rem;font-weight:800;letter-spacing:-0.02em">{_h(app_name)}</div>
  <div style="margin-top:0.4rem;opacity:0.85;font-size:1rem">UI Wireframe Document · 5 Screens</div>
  <div style="margin-top:1.25rem;display:flex;justify-content:center;gap:0.75rem;flex-wrap:wrap;font-size:0.8rem;opacity:0.75;">
    {"".join(f"<span>{i+1} · {_h(s)}</span>" + (" <span>·</span>" if i < 4 else "") for i, s in enumerate(screens))}
  </div>
</div>"""

    s1 = _screen1_dashboard(domain, app_name, c1)
    s2 = _screen2_list(domain, app_name, c1)
    s3 = _screen3_detail(domain, app_name, c1)
    s4 = _screen4_form(domain, app_name, c1)
    s5 = _screen5_settings(domain, app_name, c1)

    foot = f"""
<div style="text-align:center;padding:2rem;font-size:0.75rem;color:#94a3b8;border-top:1px solid #e2e8f0;margin-top:1rem;">
  Generated by Project Inception AI · UI Wireframe Document · {today}
</div>
</body>
</html>"""

    return head + s1 + s2 + s3 + s4 + s5 + foot
