from config import OUTPUT_DIR, APP_NAME_FIREFOX, APP_NAME_ZETTLR, APP_NAME_JABREF, APP_NAME_GODOT
from matplotlib import pyplot as plt
from matplotlib_venn import venn2

if __name__ == "__main__":
    # # Uncomment to choose the repository
    # # reponame = APP_NAME_ZETTLR
    # # reponame = APP_NAME_JABREF
    # # reponame = APP_NAME_GODOT
    # reponame = APP_NAME_FIREFOX
    #
    # A = set(range(52))
    # B = set(range(33, 87))
    #
    # fig, ax = plt.subplots(figsize=(4.5, 3))  # 👈 Control overall figure size
    # venn2([A, B], set_labels=('Our Approach', 'Ground Truth'), ax=ax)
    #
    # ax.set_aspect(0.2)  # 👈 <1 = compress horizontally (flatten)
    #
    # plt.tight_layout()
    # plt.savefig("venn_firefox_groundtruth.pdf")
    # plt.show()


    A = set(range(42))  # True positives detected by our approach
    B = set(range(29, 75))  # Ground-truth bugs

    fig, ax = plt.subplots(figsize=(4.5, 3))

    v = venn2(
        [A, B],
        set_labels=('Our Approach', 'Ground Truth'),
        ax=ax
    )

    # Set colors for the Venn diagram
    # v.get_patch_by_id('10').set_color('#55A868')  # Academic green (Our Approach)
    # v.get_patch_by_id('01').set_color('#E0E0E0')  # Light gray (Ground Truth)
    # v.get_patch_by_id('11').set_color('#B7D8C2')  # Green-gray overlap

    v.get_patch_by_id('10').set_color('#F6E4E8')  # Left: light pink from figure
    v.get_patch_by_id('01').set_color('#E1E1E1')  # Right: light gray
    v.get_patch_by_id('11').set_color('#EFD5DC')  # Intersection: slightly darker pink

    for pid in ['10', '01', '11']:
        v.get_patch_by_id(pid).set_alpha(0.85)  # Set transparency

    # 🧠 Clear, descriptive title
    ax.set_title(
        "Overlap between Bugs Detected by Our Approach (TPs)\n"
        "and Ground-Truth Introduced Bugs",
        fontsize=11
    )

    # 📝 Inline explanation (highly recommended)
    ax.text(
        0.5, -0.18,
        "Left: bugs detected by our approach (true positives only)\n"
        "Right: ground-truth introduced bugs documented in the issue tracker",
        ha='center', va='top',
        fontsize=9,
        transform=ax.transAxes
    )

    ax.set_aspect(0.22)  # Compress diagram horizontally
    plt.tight_layout()
    plt.savefig("venn_firefox_groundtruth.pdf")
    plt.show()
