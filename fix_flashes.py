import re
import os

# 1. Update app.py
with open('app.py', 'r') as f:
    content = f.read()

error_keywords = ['មិនត្រឹមត្រូវ', 'សូមចូលគណនីជាមុនសិន', 'Error', 'រកមិនឃើញ', 'បិទ', 'សូមបំពេញ', 'មានរួចហើយ', 'គ្មានសកម្មភាព', 'គ្មានសិទ្ធិ', 'មិនអាចលុប', 'not found', 'cannot', 'already']

def replacer(match):
    msg = match.group(1)
    if "', '" in msg or '", "' in msg or msg.endswith("'error'") or msg.endswith("'success'"):
        return match.group(0) # Already has category
    
    is_error = any(kw in msg for kw in error_keywords)
    category = 'error' if is_error else 'success'
    
    return f"flash({msg}, '{category}')"

new_content = re.sub(r"flash\((.*?)\)", replacer, content)

with open('app.py', 'w') as f:
    f.write(new_content)

# 2. Update templates
templates = ['login.html', 'register.html', 'admin.html', 'edit.html', 'forgot_password.html']

js_script = """
    <script>
        // Hide flash messages after 5 seconds
        setTimeout(function() {
            var flashes = document.querySelectorAll('.flashes, .flash-messages');
            flashes.forEach(function(flash) {
                flash.style.transition = 'opacity 0.5s ease';
                flash.style.opacity = '0';
                setTimeout(() => flash.remove(), 500);
            });
        }, 5000);
    </script>
</body>
"""

flash_block_flashes = """{% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
        <ul class="flashes {% if messages[0][0] == 'success' %}success{% endif %}">
            {% for category, message in messages %}
            <li>{% if category == 'success' %}✅{% else %}⚠️{% endif %} {{ message }}</li>
            {% endfor %}
        </ul>
        {% endif %}
        {% endwith %}"""

flash_block_admin = """{% with messages = get_flashed_messages(with_categories=true) %}
        {% if messages %}
        <ul class="flash-messages {% if messages[0][0] == 'error' %}error{% endif %}">
            {% for category, message in messages %}
            <li>{% if category == 'success' %}✅{% else %}⚠️{% endif %} {{ message }}</li>
            {% endfor %}
        </ul>
        {% endif %}
        {% endwith %}"""

css_flashes = """
        .flashes.success {
            background: rgba(16, 185, 129, 0.2);
            border-color: rgba(16, 185, 129, 0.3);
            color: #047857;
        }"""

css_admin = """
        .flash-messages.error {
            background: rgba(239, 68, 68, 0.1);
            border-color: rgba(239, 68, 68, 0.25);
            color: #ef4444;
        }"""

for tpl in templates:
    path = os.path.join('templates', tpl)
    with open(path, 'r') as f:
        html = f.read()
        
    # Add JS if not present
    if "Hide flash messages after 5 seconds" not in html:
        html = html.replace('</body>', js_script)
        
    # Replace get_flashed_messages block
    if tpl in ['login.html', 'register.html']:
        # They use .flashes
        html = re.sub(r"{%\s*with messages = get_flashed_messages\(\)\s*%}.*?{%\s*endwith\s*%}", flash_block_flashes, html, flags=re.DOTALL)
        if ".flashes.success {" not in html:
            html = html.replace('</style>', css_flashes + '\n    </style>')
            
    elif tpl in ['admin.html', 'edit.html']:
        # They use .flash-messages
        html = re.sub(r"{%\s*with messages = get_flashed_messages\(\)\s*%}.*?{%\s*endwith\s*%}", flash_block_admin, html, flags=re.DOTALL)
        if ".flash-messages.error {" not in html:
            html = html.replace('</style>', css_admin + '\n    </style>')
            
    with open(path, 'w') as f:
        f.write(html)

print("Done")
