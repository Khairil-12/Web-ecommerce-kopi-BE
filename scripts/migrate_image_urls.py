from app import create_app, db
from app.models.product import Product
def normalize_image_url(url: str) -> str:
    if not url:
        return url
    url = url.replace('\\', '/').strip()
    if url.startswith('/static/'):
        url = url[len('/static/') :]
    elif url.startswith('/'):
        url = url[1:]
    return url

def main():
    app = create_app()
    with app.app_context():
        products = Product.query.filter(Product.image_url.isnot(None)).all()
        updated = 0
        for p in products:
            before = p.image_url
            after = normalize_image_url(before)
            if after != before:
                p.image_url = after
                updated += 1
        if updated:
            db.session.commit()
        print(f"Processed {len(products)} products, updated {updated} rows.")
if __name__ == '__main__':
    main()