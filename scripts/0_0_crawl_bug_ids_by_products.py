from src.utils.crawl_util import CrawlUtil


if __name__ == "__main__":
    """
    crawel all bug ids under specific product and component
    save bug ids in bug_ids.txt
    """
    products = ['Firefox', 'Firefox Build System', 'Toolkit', 'Core', 'DevTools', 'WebExtensions']
    component = None

    for product in products:

        CrawlUtil.get_specific_product_component_bug_ids(product, component)
