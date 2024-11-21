import logging
from unittest.mock import MagicMock, patch

import bs4
from bs4 import BeautifulSoup

from cl.search.management.commands.update_cap_cases import Command
from cl.tests.cases import TestCase

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class UpdateCapCasesTest(TestCase):
    def setUp(self):
        super().setUp()
        self.command = Command()

    def test_update_cap_html_with_cl_xml_simple(self):
        # Simple case: Update various paragraph types
        cap_html = """
        <section class="casebody">
            <article class="opinion" data-type="majority">
                <p class="author" id="b1">AUTHOR NAME</p>
                <p id="b2">Some opinion text</p>
                <p class="summary" id="b3">Case summary</p>
                <p id="b4">More text</p>
            </article>
        </section>
        """

        cl_xml_list = [
            {
                "id": 1,
                "type": "majority",
                "xml": """
            <opinion type="majority">
                <author id="b1">AUTHOR NAME</author>
                <p id="b2">Some opinion text</p>
                <summary id="b3">Case summary</summary>
                <aside id="b4">More text</aside>
            </opinion>
            """,
            }
        ]

        processed_opinions, changes = self.command.update_cap_html_with_cl_xml(
            cap_html, cl_xml_list
        )

        print(f"Processed opinions: {processed_opinions}")

        self.assertEqual(len(processed_opinions), 1)

        soup = BeautifulSoup(processed_opinions[0]["xml"], "xml")
        print(f"Parsed XML: {soup.prettify()}")

        # Check the overall structure
        opinion_tag = soup.find("opinion")
        print(f"Opinion tag: {opinion_tag}")
        self.assertIsNotNone(opinion_tag, "Opinion tag should exist")
        self.assertEqual(
            opinion_tag.get("type"),
            "majority",
            "Opinion type should be majority",
        )
        self.assertEqual(
            opinion_tag.get("data-type"),
            "majority",
            "Opinion data-type should be majority",
        )

        author_tag = opinion_tag.find("author")
        print(f"Author tag: {author_tag}")
        self.assertIsNotNone(author_tag, "Author tag should exist")
        self.assertEqual(
            author_tag.get("id"), "b1", "Author tag should have id 'b1'"
        )
        self.assertEqual(
            author_tag.text.strip(),
            "AUTHOR NAME",
            "Author name should be correct",
        )

        p_tag = opinion_tag.find("p", id="b2")
        print(f"P tag: {p_tag}")
        self.assertIsNotNone(p_tag, "P tag with id 'b2' should exist")
        self.assertEqual(
            p_tag.text.strip(),
            "Some opinion text",
            "P tag text should be correct",
        )

        summary_tag = opinion_tag.find("summary")
        print(f"Summary tag: {summary_tag}")
        self.assertIsNotNone(summary_tag, "Summary tag should exist")
        self.assertEqual(
            summary_tag.get("id"), "b3", "Summary tag should have id 'b3'"
        )
        self.assertEqual(
            summary_tag.text.strip(),
            "Case summary",
            "Summary text should be correct",
        )

        aside_tag = opinion_tag.find("aside", id="b4")
        print(f"Aside tag: {aside_tag}")
        self.assertIsNotNone(aside_tag, "Aside tag with id 'b4' should exist")
        self.assertEqual(
            aside_tag.text.strip(),
            "More text",
            "Aside tag text should be correct",
        )

        # Check that there are no class attributes left
        self.assertIsNone(
            soup.find(attrs={"class": True}),
            "There should be no elements with class attributes",
        )

        # Check that there are only four direct children of the opinion tag
        self.assertEqual(
            len(opinion_tag.find_all(recursive=False)),
            4,
            "Opinion tag should have exactly 4 direct children",
        )

        # Verify the order of elements
        children = [
            child
            for child in opinion_tag.children
            if isinstance(child, bs4.element.Tag)
        ]
        print("Filtered children of opinion tag:")
        for i, child in enumerate(children):
            print(f"{i}: <{child.name}>")

        self.assertTrue(
            len(children) >= 4,
            f"Opinion tag should have at least 4 child tags, but has {len(children)}",
        )
        self.assertEqual(
            children[0].name,
            "author",
            f"First child tag should be an author tag, but is <{children[0].name}>",
        )
        self.assertEqual(
            children[1].name,
            "p",
            f"Second child tag should be a p tag, but is <{children[1].name}>",
        )
        self.assertEqual(
            children[2].name,
            "summary",
            f"Third child tag should be a summary tag, but is <{children[2].name}>",
        )
        self.assertEqual(
            children[3].name,
            "aside",
            f"Fourth child tag should be an aside tag, but is <{children[3].name}>",
        )

        print("All assertions passed successfully!")

    def test_update_cap_html_with_no_opinion_content(self):
        # Case: CL XML includes an opinion not present in CAP HTML
        cap_html = """
        <section class="casebody">
            <article class="opinion" data-type="majority">
                <p class="author" id="b1">AUTHOR NAME</p>
                <p id="b2">Some opinion text</p>
            </article>
        </section>
        """

        cl_xml_list = [
            {
                "id": 1,
                "type": "majority",
                "xml": """
        <opinion type="majority">
            <author id="b1">AUTHOR NAME</author>
            <p id="b2">Some opinion text</p>
        </opinion>
        """,
            },
            {
                "id": 2,
                "type": "concurrence",
                "xml": """
        <opinion type="concurrence">
            <author>CONCURRING JUDGE</author>
            <p>No opinion found.</p>
        </opinion>
        """,
            },
        ]

        processed_opinions, changes = self.command.update_cap_html_with_cl_xml(
            cap_html, cl_xml_list
        )

        self.assertEqual(len(processed_opinions), 2)

        # Check the majority opinion
        majority_soup = BeautifulSoup(processed_opinions[0]["xml"], "xml")
        majority_opinion = majority_soup.find("opinion")
        self.assertEqual(majority_opinion["type"], "majority")
        self.assertEqual(len(majority_opinion.find_all(recursive=False)), 2)

        concurrence_soup = BeautifulSoup(processed_opinions[1]["xml"], "xml")
        concurrence_opinion = concurrence_soup.find("opinion")
        self.assertEqual(concurrence_opinion["type"], "concurrence")
        self.assertEqual(len(concurrence_opinion.find_all(recursive=False)), 2)
        self.assertEqual(
            concurrence_opinion.author.text.strip(), "CONCURRING JUDGE"
        )
        self.assertEqual(
            concurrence_opinion.p.text.strip(), "No opinion found."
        )

    def test_update_cap_html_with_extra_cap_opinion(self):
        # Case: CAP HTML includes an opinion not present in CL XML
        cap_html = """
        <section class="casebody">
            <article class="opinion" data-type="majority">
                <p class="author" id="b1">AUTHOR NAME</p>
                <p id="b2">Some opinion text</p>
            </article>
            <article class="opinion" data-type="dissent">
                <p class="author" id="b3">DISSENTING JUDGE</p>
                <p id="b4">Dissent text</p>
            </article>
        </section>
        """

        cl_xml_list = [
            {
                "id": 1,
                "type": "majority",
                "xml": """
        <opinion type="majority">
            <author id="b1">UPDATED AUTHOR NAME</author>
            <p id="b2">Updated opinion text</p>
        </opinion>
        """,
            }
        ]

        processed_opinions, changes = self.command.update_cap_html_with_cl_xml(
            cap_html, cl_xml_list
        )

        self.assertEqual(
            len(processed_opinions),
            1,
            "Only the majority opinion should be processed",
        )

        # Check that only the majority opinion is in the processed opinions
        self.assertEqual(
            processed_opinions[0]["type"],
            "majority",
            "Only the majority opinion should be in the processed opinions",
        )

        # Check the content of the majority opinion
        majority_soup = BeautifulSoup(processed_opinions[0]["xml"], "xml")
        self.assertEqual(
            majority_soup.author.text,
            "AUTHOR NAME",
            "The author name should be preserved from CAP HTML",
        )
        self.assertEqual(
            majority_soup.p.text,
            "Some opinion text",
            "The opinion text should be preserved from CAP HTML",
        )

    def test_update_cap_html_with_extra_cap_content(self):
        # Case: CAP HTML includes extra content within a matching opinion
        cap_html = """
        <section class="casebody">
            <article class="opinion" data-type="majority">
                <p class="author" id="b1">AUTHOR NAME</p>
                <p id="b2">Some opinion text</p>
                <p id="b3">Extra CAP content</p>
            </article>
        </section>
        """

        cl_xml_list = [
            {
                "id": 1,
                "type": "majority",
                "xml": """
        <opinion type="majority">
            <author id="b1">UPDATED AUTHOR NAME</author>
            <p id="b2">Updated opinion text</p>
        </opinion>
        """,
            }
        ]

        processed_opinions, changes = self.command.update_cap_html_with_cl_xml(
            cap_html, cl_xml_list
        )

        self.assertEqual(
            len(processed_opinions), 1, "One opinion should be processed"
        )

        majority_opinion = processed_opinions[0]
        self.assertEqual(majority_opinion["type"], "majority")

        majority_soup = BeautifulSoup(majority_opinion["xml"], "xml")

        self.assertEqual(
            majority_soup.author.text,
            "AUTHOR NAME",
            "The author name should be preserved from CAP HTML",
        )
        self.assertEqual(
            majority_soup.find("p", id="b2").text,
            "Some opinion text",
            "The opinion text should be preserved from CAP HTML",
        )
        self.assertIsNotNone(
            majority_soup.find("p", id="b3"),
            "Extra CAP content should be preserved",
        )
        self.assertEqual(
            majority_soup.find("p", id="b3").text,
            "Extra CAP content",
            "Extra CAP content should be unchanged",
        )

    def test_convert_html_to_xml_simple(self):
        html_content = """
        <div class="opinion">
            <p class="author">AUTHOR NAME</p>
            <p class="paragraph">Some opinion text</p>
            <div class="footnote">A footnote</div>
        </div>
        """

        expected_xml = """
        <opinion>
            <author>AUTHOR NAME</author>
            <paragraph>Some opinion text</paragraph>
            <footnote>A footnote</footnote>
        </opinion>
        """

        result = self.command.convert_html_to_xml(html_content)

        # Normalize whitespace for comparison
        result = " ".join(result.split())
        expected_xml = " ".join(expected_xml.split())

        self.assertEqual(
            result,
            expected_xml,
            "The converted XML does not match the expected output",
        )

        self.assertNotIn(
            'class="', result, "Class attributes should be removed"
        )
        self.assertIn(
            "<opinion>",
            result,
            "The root element should be renamed to 'opinion'",
        )
        self.assertIn(
            "<author>",
            result,
            "The 'author' class should be converted to a tag",
        )
        self.assertIn(
            "<paragraph>",
            result,
            "The 'paragraph' class should be converted to a tag",
        )
        self.assertIn(
            "<footnote>",
            result,
            "The 'footnote' class should be converted to a tag",
        )

    @patch(
        "cl.search.management.commands.update_cap_cases.Command.fetch_cap_html"
    )
    @patch(
        "cl.search.management.commands.update_cap_cases.Command.fetch_cl_xml"
    )
    @patch(
        "cl.search.management.commands.update_cap_cases.Command.update_cap_html_with_cl_xml"
    )
    @patch(
        "cl.search.management.commands.update_cap_cases.Command.save_updated_xml"
    )
    @patch(
        "cl.search.management.commands.update_cap_cases.Command.update_cluster_headmatter"
    )
    def test_process_crosswalk_simple(
        self,
        mock_update_headmatter,
        mock_save_xml,
        mock_update_html,
        mock_fetch_cl,
        mock_fetch_cap,
    ):
        mock_fetch_cap.return_value = """
        <html>
            <body>
                <section class="casebody">
                    <article class="opinion" data-type="majority">
                        <p>Some case content</p>
                    </article>
                </section>
            </body>
        </html>
        """
        mock_fetch_cl.return_value = (
            MagicMock(),
            [{"id": 1, "type": "opinion", "xml": "<opinion>CL XML</opinion>"}],
        )
        mock_update_html.return_value = (
            [{"id": 1, "type": "opinion", "xml": "<updated>XML</updated>"}],
            ["change"],
        )

        crosswalk_content = [
            {
                "cap_path": "path/to/cap",
                "cl_cluster_id": 123,
                "cap_case_id": 8118054,
            }
        ]

        with patch("builtins.open", MagicMock()):
            with patch("json.load", return_value=crosswalk_content):
                # Set self.crosswalk_dir to a test-specific value
                self.command.crosswalk_dir = "/test/crosswalk"
                # Call the method under test
                self.command.process_crosswalk("test_reporter")

        mock_fetch_cap.assert_called_once_with("path/to/cap")
        mock_fetch_cl.assert_called_once_with(123)
        mock_update_html.assert_called_once()
        mock_save_xml.assert_called_once()
        mock_update_headmatter.assert_called_once()