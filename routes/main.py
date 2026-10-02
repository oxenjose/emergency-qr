import re
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, Response
from database.models import create_contact, get_contact, update_contact, verify_pin
from routes.qr import decode_qr_from_image

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('index.html')


@main_bp.route('/create', methods=['GET', 'POST'])
def create():
    if request.method == 'POST':
        owner_name = request.form['owner_name'].strip()
        label = request.form.get('label', '').strip()[:40]
        name1 = request.form['name1'].strip()
        phone1 = request.form['phone1'].strip()
        name2 = request.form.get('name2', '').strip()
        phone2 = request.form.get('phone2', '').strip()
        name3 = request.form.get('name3', '').strip()
        phone3 = request.form.get('phone3', '').strip()
        pin = request.form['pin']

        if not owner_name or not name1 or not phone1 or not pin:
            flash('Owner name, Contact 1 and PIN are required.')
            return redirect(url_for('main.create'))

        contact_id = create_contact(
            owner_name, label, name1, phone1, name2, phone2, name3, phone3, pin
        )
        return redirect(url_for('main.created', contact_id=contact_id))

    return render_template('create.html')


@main_bp.route('/created/<contact_id>')
def created(contact_id):
    contact = get_contact(contact_id)
    if not contact:
        return redirect(url_for('main.index'))
    return render_template('created.html', contact=contact)


@main_bp.route('/view/<contact_id>')
def view(contact_id):
    contact = get_contact(contact_id)
    if not contact:
        return render_template('qr_not_found.html'), 404
    return render_template('view.html', contact=contact)


@main_bp.route('/edit/<contact_id>', methods=['GET', 'POST'])
def edit(contact_id):
    contact = get_contact(contact_id)
    if not contact:
        return render_template('qr_not_found.html'), 404

    if request.method == 'POST':
        pin = request.form['pin']
        if verify_pin(contact_id, pin):
            session['edit_id'] = contact_id
            return redirect(url_for('main.edit', contact_id=contact_id))
        else:
            flash('Incorrect PIN')
            return redirect(url_for('main.edit', contact_id=contact_id))

    authenticated = session.get('edit_id') == contact_id
    return render_template('edit.html', contact=contact, authenticated=authenticated)


@main_bp.route('/update/<contact_id>', methods=['POST'])
def update(contact_id):
    if session.get('edit_id') != contact_id:
        return "Unauthorized", 403
    contact = get_contact(contact_id)
    if not contact:
        return render_template('qr_not_found.html'), 404

    owner_name = request.form['owner_name'].strip()
    label = request.form.get('label', '').strip()[:40]
    name1 = request.form['name1'].strip()
    phone1 = request.form['phone1'].strip()
    name2 = request.form.get('name2', '').strip()
    phone2 = request.form.get('phone2', '').strip()
    name3 = request.form.get('name3', '').strip()
    phone3 = request.form.get('phone3', '').strip()

    update_contact(contact_id, owner_name, label, name1, phone1, name2, phone2, name3, phone3)
    session.pop('edit_id', None)
    flash('Contacts updated successfully')
    return redirect(url_for('main.created', contact_id=contact_id))


@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        flash('Thanks for reaching out! We will get back to you soon.')
        return redirect(url_for('main.contact'))
    return render_template('contact.html')


@main_bp.route('/privacy')
def privacy():
    return render_template('privacy.html')


@main_bp.route('/check', methods=['GET', 'POST'])
def check():
    if request.method == 'POST':
        file = request.files.get('qr_image')

        if not file or file.filename == '':
            flash('Please select an image or PDF file.')
            return redirect(url_for('main.check'))

        image_bytes = file.read()
        decoded = decode_qr_from_image(image_bytes, filename=file.filename)

        if not decoded:
            flash('Could not find a QR code in that file. Try a clearer photo or a different angle.')
            return redirect(url_for('main.check'))

        match = re.search(
            r'/view/([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})',
            decoded
        )
        if not match:
            flash('That QR code does not belong to Emergency QR.')
            return redirect(url_for('main.check'))

        contact_id = match.group(1)
        contact = get_contact(contact_id)
        if not contact:
            flash('This QR code is not registered in our system.')
            return redirect(url_for('main.check'))

        flash(f'QR recognized — contacts for {contact["owner_name"]}.')
        return redirect(url_for('main.view', contact_id=contact_id))

    return render_template('check.html')


# ------------------------------------------------------------------
# SEO: robots.txt and sitemap.xml
# ------------------------------------------------------------------

@main_bp.route('/robots.txt')
def robots():
    content = render_template('robots.txt')
    return Response(content, mimetype='text/plain')


@main_bp.route('/sitemap.xml')
def sitemap():
    content = render_template('sitemap.xml')
    return Response(content, mimetype='application/xml')