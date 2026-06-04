"""
高中全科教材 PDF 批量下载脚本
================================
下载9大主科（数学/物理/化学/生物/语文/英语/历史/地理/政治）
人教版/统编版全套教材，共50本。
无需登录，通过 CDN 直链下载。

用法：
    python download_all_hs.py
    python download_all_hs.py --subject 数学     # 只下载数学
    python download_all_hs.py --dry-run          # 只显示列表，不实际下载
"""

import os
import sys
import time
import logging
import argparse
import requests
from pathlib import Path

for k in ["http_proxy", "https_proxy", "HTTP_PROXY", "HTTPS_PROXY", "no_proxy", "NO_PROXY"]:
    os.environ.pop(k, None)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
PDF_DIR = BASE_DIR / "cache" / "pdfs" / "high_school"

# CDN 镜像列表（按优先级排序）
CDN_MIRRORS = [
    "https://r1-ndr.ykt.cbern.com.cn/edu_product/esp/assets_document/{id}.pkg/pdf.pdf",
    "https://r2-ndr.ykt.cbern.com.cn/edu_product/esp/assets_document/{id}.pkg/pdf.pdf",
    "https://r3-ndr.ykt.cbern.com.cn/edu_product/esp/assets_document/{id}.pkg/pdf.pdf",
    "https://c1.ykt.cbern.com.cn/edu_product/esp/assets_document/{id}.pkg/pdf.pdf",
]

# ==================== 高中全科教材列表（50本） ====================
TEXTBOOK_LIST = [
    # ===== 数学（人教A版）=====
    {"id": "6e764703-6e5e-4ea3-9462-34652c2678ef", "subject": "数学", "title": "数学（A版）必修 第一册", "filename": "math_a_bi1"},
    {"id": "d296fc79-8d47-4b18-862c-6df49adc2ce0", "subject": "数学", "title": "数学（A版）必修 第二册", "filename": "math_a_bi2"},
    {"id": "d0fd2c1f-6b4f-43f0-8229-de0a53b197df", "subject": "数学", "title": "数学（A版）选择性必修 第一册", "filename": "math_a_sel1"},
    {"id": "99c1fb5b-d1e0-4238-90b9-a573ab84bf08", "subject": "数学", "title": "数学（A版）选择性必修 第二册", "filename": "math_a_sel2"},
    {"id": "ffaba6c3-497d-47b0-b91a-784f43625507", "subject": "数学", "title": "数学（A版）选择性必修 第三册", "filename": "math_a_sel3"},

    # ===== 物理（人教版）=====
    {"id": "708256b6-6f06-4d14-89c7-4df16dfe3b81", "subject": "物理", "title": "物理必修 第一册", "filename": "physics_bi1"},
    {"id": "55baa3cc-156f-4358-8e28-bfa21a864450", "subject": "物理", "title": "物理必修 第二册", "filename": "physics_bi2"},
    {"id": "dcd8cc6b-5380-4008-a2d0-a061f24d34dd", "subject": "物理", "title": "物理必修 第三册", "filename": "physics_bi3"},
    {"id": "346c3c04-1663-472c-849e-ff876dcf293f", "subject": "物理", "title": "物理选择性必修 第一册", "filename": "physics_sel1"},
    {"id": "2ee7d7fa-1920-4d37-a179-91d5fd59b8c1", "subject": "物理", "title": "物理选择性必修 第二册", "filename": "physics_sel2"},
    {"id": "2109c25c-2e52-4da3-8ab3-18cbe632ec11", "subject": "物理", "title": "物理选择性必修 第三册", "filename": "physics_sel3"},

    # ===== 化学（人教版）=====
    {"id": "5cd19072-e40d-4a73-8580-7b7ada5d4005", "subject": "化学", "title": "化学必修 第一册", "filename": "chemistry_bi1"},
    {"id": "07f7d663-a867-4eb6-ad39-03b55dbd4a65", "subject": "化学", "title": "化学必修 第二册", "filename": "chemistry_bi2"},
    {"id": "3502fe81-b23e-4f68-aa3d-7921e7932ec9", "subject": "化学", "title": "化学选择性必修1 化学反应原理", "filename": "chemistry_sel1"},
    {"id": "b82cefe7-d631-4bde-baf9-352ca033cba4", "subject": "化学", "title": "化学选择性必修2 物质结构与性质", "filename": "chemistry_sel2"},
    {"id": "c561d8ee-7c06-4cb1-9a4d-e34036f02d53", "subject": "化学", "title": "化学选择性必修3 有机化学基础", "filename": "chemistry_sel3"},

    # ===== 生物（人教版）=====
    {"id": "9d522562-b529-446c-9b5b-084812beee6e", "subject": "生物", "title": "生物学必修1 分子与细胞", "filename": "biology_bi1"},
    {"id": "f89f0368-11c8-4a21-a767-a9102c9ce872", "subject": "生物", "title": "生物学必修2 遗传与进化", "filename": "biology_bi2"},
    {"id": "ec6ab12c-0b06-43a5-bf62-ee90b619f607", "subject": "生物", "title": "生物学选择性必修1 稳态与调节", "filename": "biology_sel1"},
    {"id": "825baab7-f0ea-4a90-9b4a-513f338e2484", "subject": "生物", "title": "生物学选择性必修2 生物与环境", "filename": "biology_sel2"},
    {"id": "d12ff6b6-b6cd-444a-9749-4642aa350482", "subject": "生物", "title": "生物学选择性必修3 生物技术与工程", "filename": "biology_sel3"},

    # ===== 语文（统编版）=====
    {"id": "b8e9a3fe-dae7-49c0-86cb-d146f883fd8e", "subject": "语文", "title": "语文必修 上册", "filename": "chinese_bi_up"},
    {"id": "9085151a-b698-4b28-8c00-2c4aaf0c91ad", "subject": "语文", "title": "语文必修 下册", "filename": "chinese_bi_down"},
    {"id": "3b7a3baf-4e1e-4380-b2cc-3bf330d00cc3", "subject": "语文", "title": "语文选择性必修 上册", "filename": "chinese_sel_up"},
    {"id": "da694670-f25b-46a0-9c3f-a31f5a2f131a", "subject": "语文", "title": "语文选择性必修 中册", "filename": "chinese_sel_mid"},
    {"id": "2de54e6d-1f82-4fdc-9f26-c94dfed9c5af", "subject": "语文", "title": "语文选择性必修 下册", "filename": "chinese_sel_down"},

    # ===== 英语（人教版）=====
    {"id": "8e62f140-1990-411e-8831-59a69bb53c1d", "subject": "英语", "title": "英语必修 第一册", "filename": "english_bi1"},
    {"id": "144425f4-87a0-4a3a-82b7-ea7be112856c", "subject": "英语", "title": "英语必修 第二册", "filename": "english_bi2"},
    {"id": "bf54b36f-4c75-4c91-8b9c-53ce15e4f903", "subject": "英语", "title": "英语必修 第三册", "filename": "english_bi3"},
    {"id": "ec1adf40-7bf0-48a4-9902-89162f59277d", "subject": "英语", "title": "英语选择性必修 第一册", "filename": "english_sel1"},
    {"id": "0d537335-d02c-4774-85e2-7554c86fea7e", "subject": "英语", "title": "英语选择性必修 第二册", "filename": "english_sel2"},
    {"id": "671e59b0-608f-49c6-8f23-e076decf27e2", "subject": "英语", "title": "英语选择性必修 第三册", "filename": "english_sel3"},
    {"id": "5f0829b2-fc05-479b-a51e-47f871598eba", "subject": "英语", "title": "英语选择性必修 第四册", "filename": "english_sel4"},

    # ===== 历史（统编版）=====
    {"id": "aadd94cd-2d05-4716-aa25-dab70c9fc7a4", "subject": "历史", "title": "历史必修 中外历史纲要（上）", "filename": "history_bi_up"},
    {"id": "ec47ff37-71bf-4a88-b4da-f934d0cc40ea", "subject": "历史", "title": "历史必修 中外历史纲要（下）", "filename": "history_bi_down"},
    {"id": "7786158e-01d7-4544-a358-5759664c78ea", "subject": "历史", "title": "历史选择性必修1 国家制度与社会治理", "filename": "history_sel1"},
    {"id": "183e709c-5a7f-44b9-a633-51eb0cd81f0b", "subject": "历史", "title": "历史选择性必修2 经济与社会生活", "filename": "history_sel2"},
    {"id": "f2442c65-9148-47ee-9d57-37e6f801fdb4", "subject": "历史", "title": "历史选择性必修3 文化交流与传播", "filename": "history_sel3"},

    # ===== 地理（人教版）=====
    {"id": "e2c5fb9c-9a73-4f1a-8fb5-10b1299c7f5c", "subject": "地理", "title": "地理必修 第一册", "filename": "geography_bi1"},
    {"id": "8452d2cf-1a23-4656-84b9-26616cbd2eff", "subject": "地理", "title": "地理必修 第二册", "filename": "geography_bi2"},
    {"id": "373d48bd-c1b4-4edd-b148-628713692ba3", "subject": "地理", "title": "地理选择性必修1 自然地理基础", "filename": "geography_sel1"},
    {"id": "db7e6c9c-44b3-4818-96c6-ce81dabb3cc7", "subject": "地理", "title": "地理选择性必修2 区域发展", "filename": "geography_sel2"},
    {"id": "f07377f5-2ced-4d59-a59d-fe3b37800ead", "subject": "地理", "title": "地理选择性必修3 资源、环境与国家安全", "filename": "geography_sel3"},

    # ===== 政治（统编版）=====
    {"id": "c7c07640-970b-4def-814a-0f77eba4a2d9", "subject": "政治", "title": "思想政治必修1 中国特色社会主义", "filename": "politics_bi1"},
    {"id": "e36cf7c0-c787-4b34-ba7a-84a78baac331", "subject": "政治", "title": "思想政治必修2 经济与社会", "filename": "politics_bi2"},
    {"id": "507cf8b4-327e-41ad-9f6d-babb59f5eef1", "subject": "政治", "title": "思想政治必修3 政治与法治", "filename": "politics_bi3"},
    {"id": "561cdda2-8f90-4b13-b987-8d8c3bb9e554", "subject": "政治", "title": "思想政治必修4 哲学与文化", "filename": "politics_bi4"},
    {"id": "9cee6cbd-4ce9-43a2-b884-895dafd832af", "subject": "政治", "title": "思想政治选择性必修1 当代国际政治与经济", "filename": "politics_sel1"},
    {"id": "acc5bf16-92b5-47c7-b57b-b7f4eb5f2199", "subject": "政治", "title": "思想政治选择性必修2 法律与生活", "filename": "politics_sel2"},
    {"id": "33a1cf09-b3e4-4874-95f4-25d38a5847c3", "subject": "政治", "title": "思想政治选择性必修3 逻辑与思维", "filename": "politics_sel3"},
]


def download_one(book: dict, sess: requests.Session) -> bool:
    """下载单本教材 PDF，已存在则跳过"""
    out_path = PDF_DIR / book["subject"] / f"{book['filename']}.pdf"

    if out_path.exists() and out_path.stat().st_size > 100_000:
        log.info(f"  ✅ 已缓存：{out_path.name} ({out_path.stat().st_size/1024/1024:.1f} MB)")
        return True

    book_id = book["id"]
    proxies = {"http": None, "https": None}
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    for url_tmpl in CDN_MIRRORS:
        url = url_tmpl.format(id=book_id)
        try:
            r = sess.head(url, timeout=15, proxies=proxies, headers=headers)
            if r.status_code != 200:
                continue

            size_mb = int(r.headers.get("Content-Length", 0)) / 1024 / 1024
            log.info(f"  下载中：{book['title']} ({size_mb:.1f} MB)")

            out_path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = out_path.with_suffix(".tmp")

            r2 = sess.get(url, stream=True, timeout=600, proxies=proxies, headers=headers)
            r2.raise_for_status()

            downloaded = 0
            with open(tmp_path, "wb") as f:
                for chunk in r2.iter_content(chunk_size=65536):
                    f.write(chunk)
                    downloaded += len(chunk)
                    if downloaded > 0 and downloaded % (20 * 1024 * 1024) < 65536:
                        log.info(f"    进度：{downloaded/1024/1024:.0f} MB")

            tmp_path.rename(out_path)
            log.info(f"  ✅ 完成：{out_path.name} ({out_path.stat().st_size/1024/1024:.1f} MB)")
            return True

        except Exception as e:
            log.debug(f"  {url[:60]} 失败: {e}")
            continue

    log.error(f"  ❌ 全部镜像失败：{book['title']}")
    return False


def main():
    parser = argparse.ArgumentParser(description="高中全科教材 PDF 批量下载")
    parser.add_argument("--subject", help="只下载指定学科（如：数学）", default=None)
    parser.add_argument("--dry-run", action="store_true", help="只列出待下载列表，不实际下载")
    parser.add_argument("--delay", type=float, default=1.5, help="每本之间的间隔秒数（默认1.5）")
    args = parser.parse_args()

    books = TEXTBOOK_LIST
    if args.subject:
        books = [b for b in books if b["subject"] == args.subject]
        if not books:
            log.error(f"未找到学科：{args.subject}，可用学科：数学/物理/化学/生物/语文/英语/历史/地理/政治")
            sys.exit(1)

    # 统计已缓存
    cached = [b for b in books if (PDF_DIR / b["subject"] / f"{b['filename']}.pdf").exists()
              and (PDF_DIR / b["subject"] / f"{b['filename']}.pdf").stat().st_size > 100_000]
    pending = [b for b in books if b not in cached]

    log.info("=" * 60)
    log.info(f"📚 高中全科教材下载器")
    log.info(f"   总计：{len(books)} 本  已缓存：{len(cached)} 本  待下载：{len(pending)} 本")
    log.info(f"   保存目录：{PDF_DIR}")
    log.info("=" * 60)

    if args.dry_run:
        for b in books:
            p = PDF_DIR / b["subject"] / f"{b['filename']}.pdf"
            status = "✅已有" if p.exists() and p.stat().st_size > 100_000 else "⬇️待下"
            log.info(f"  {status} [{b['subject']}] {b['title']}")
        return

    if not pending:
        log.info("所有教材已缓存，无需下载。")
        return

    sess = requests.Session()
    ok_count = 0
    fail_list = []

    for i, book in enumerate(books):
        log.info(f"\n[{i+1}/{len(books)}] [{book['subject']}] {book['title']}")
        ok = download_one(book, sess)
        if ok:
            ok_count += 1
        else:
            fail_list.append(book)
        if i < len(books) - 1:
            time.sleep(args.delay)

    log.info("\n" + "=" * 60)
    log.info(f"🎉 下载完成：{ok_count}/{len(books)} 本成功")
    if fail_list:
        log.warning(f"失败 {len(fail_list)} 本：")
        for b in fail_list:
            log.warning(f"  [{b['subject']}] {b['title']}")
    log.info(f"PDF 保存在：{PDF_DIR}")
    log.info("下一步：python build_knowledge_base.py")


if __name__ == "__main__":
    main()
