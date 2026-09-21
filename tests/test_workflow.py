import sys
from pathlib import Path
import pytest

APP = Path(__file__).resolve().parents[1] / 'advanced_ai_agents/multi_agent_apps/ai_email_gtm_outreach_agent'
sys.path.insert(0, str(APP))
from agents import Companies, Contacts, Research, Email, Workflow, StageError, validate_contacts, markdown_export

SOURCE = {'title': 'Example', 'url': 'https://example.com', 'text': 'Alex is head of sales. alex@example.com'}


def contact(email='alex@example.com'):
    return Contacts(contacts=[dict(name='Alex', role='Head of Sales', email=email, email_status='published', source_ids=[1])])


def test_email_labels_and_unsupported_contacts():
    assert validate_contacts(contact(), [SOURCE], 'https://example.com', False)[0]['email_status'] == 'published'
    assert validate_contacts(contact('alex.smith@example.com'), [SOURCE], 'https://example.com', False)[0]['email'] is None
    assert validate_contacts(contact('alex.smith@example.com'), [SOURCE], 'https://example.com', True)[0]['email_status'] == 'inferred'
    assert validate_contacts(contact('alex@other.com'), [SOURCE], 'https://example.com', True)[0]['email'] is None
    assert validate_contacts(contact(), [], 'https://example.com', True) == []


class FakeWorkflow(Workflow):
    def __init__(self):
        self.calls = []
        self.fail = True

    def search(self, *args, **kwargs):
        return [SOURCE]

    def ask(self, task, schema, data):
        self.calls.append(schema.__name__)
        if schema is Companies:
            return Companies(companies=[dict(name='Example', website='https://example.com', fit='Relevant', source_ids=[1])])
        if schema is Contacts:
            return contact()
        if schema is Research:
            return Research(insights=[dict(finding='A finding', relevance='A reason', source_ids=[1])], limitations='No relevant Reddit source.')
        if self.fail:
            raise StageError('Temporary outage')
        return Email(subject='A question', body='Hello Alex, can we talk?')


def test_pipeline_resume_and_export():
    state = {'config': dict(targeting='SaaS', offering='Sales tools', count=1, style='Casual', allow_inferred=False)}
    worker = FakeWorkflow()
    with pytest.raises(StageError):
        worker.run(state, lambda *args: None)
    assert 'research' in state['companies'][0]
    worker.fail = False
    worker.run(state, lambda *args: None)
    assert state['complete']
    assert worker.calls.count('Companies') == 1
    assert worker.calls.count('Contacts') == 1
    assert worker.calls.count('Research') == 1
    assert len(state['companies'][0]['emails']) == 1
    assert 'Hello Alex' in markdown_export(state)


def test_streamlit_empty_and_validation():
    from streamlit.testing.v1 import AppTest
    app = AppTest.from_file(str(APP / 'ai_email_gtm_outreach_agent.py')).run()
    assert not app.exception
    app.button[0].click().run()
    assert 'Add both' in app.error[0].value
    assert not app.exception


def test_streamlit_results(monkeypatch):
    import agents
    from streamlit.testing.v1 import AppTest
    monkeypatch.setattr(agents.Workflow, '__init__', lambda self, *a: None)
    monkeypatch.setattr(agents.Workflow, 'search', FakeWorkflow.search)
    def ask(self, *args):
        self.calls = []
        self.fail = False
        return FakeWorkflow.ask(self, *args)
    monkeypatch.setattr(agents.Workflow, 'ask', ask)
    monkeypatch.setattr(agents.Workflow, 'close', lambda self: None)
    app = AppTest.from_file(str(APP / 'ai_email_gtm_outreach_agent.py')).run()
    app.text_input[0].set_value('test-key')
    app.text_input[1].set_value('test-key')
    app.text_area[0].set_value('SaaS companies')
    app.text_area[1].set_value('Sales tools')
    app.button[0].click().run()
    assert not app.exception
    assert app.session_state.run['complete']
    assert len(app.code) == 1
