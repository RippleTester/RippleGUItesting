from config import OUTPUT_DIR, APP_NAME_FIREFOX, APP_NAME_ZETTLR, APP_NAME_JABREF, APP_NAME_GODOT
from matplotlib import pyplot as plt
from matplotlib_venn import venn2

if __name__ == "__main__":
    # # reponame = APP_NAME_ZETTLR
    # # reponame = APP_NAME_JABREF
    # # reponame = APP_NAME_GODOT
    # reponame = APP_NAME_FIREFOX
    #
    # A = set(range(52))
    # B = set(range(33, 87))
    #
    # fig, ax = plt.subplots(figsize=(4.5, 3))  # 👈 控制整体空间
    # venn2([A, B], set_labels=('Our Approach', 'Ground Truth'), ax=ax)
    #
    # ax.set_aspect(0.2)  # 👈 小于 1 = 横向压缩（变扁）
    #
    # plt.tight_layout()
    # plt.savefig("venn_firefox_groundtruth.pdf")
    # plt.show()


    A = set(range(42))  # TP detected bugs
    B = set(range(29, 75))  # Ground-truth bugs

    fig, ax = plt.subplots(figsize=(4.5, 3))

    v = venn2(
        [A, B],
        set_labels=('Our Approach', 'Ground Truth'),
        ax=ax
    )

    v.get_patch_by_id('10').set_color('#55A868')  # 学术绿（Our Approach）
    v.get_patch_by_id('01').set_color('#E0E0E0')  # 浅灰（Ground Truth）
    v.get_patch_by_id('11').set_color('#B7D8C2')  # 绿灰交集

    for pid in ['10', '01', '11']:
        v.get_patch_by_id(pid).set_alpha(0.85)

    # 🧠 明确语义的标题
    ax.set_title(
        "Overlap between Bugs Detected by Our Approach (TPs)\n"
        "and Ground-Truth Introduced Bugs",
        fontsize=11
    )

    # 📝 图内注释（强烈推荐）
    ax.text(
        0.5, -0.18,
        "Left: bugs detected by our approach (true positives only)\n"
        "Right: ground-truth introduced bugs documented in the issue tracker",
        ha='center', va='top',
        fontsize=9,
        transform=ax.transAxes
    )

    ax.set_aspect(0.22)
    plt.tight_layout()
    plt.savefig("venn_firefox_groundtruth.pdf")
    plt.show()


