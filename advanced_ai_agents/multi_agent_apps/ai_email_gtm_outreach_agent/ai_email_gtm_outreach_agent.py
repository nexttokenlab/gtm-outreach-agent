"""Run with: streamlit run <path to this file>."""
import json
import os

import streamlit as st
from agents import StageError, Workflow, markdown_export, referenced

st.set_page_config(page_title='GTM Outreach', page_icon='✉', layout='wide')
st.title('GTM Outreach')
st.write('Find the right companies. Understand their business. Start a relevant conversation.')

with st.sidebar:
    st.header('Connections')
    openai_key = st.text_input('OpenAI API key', type='password', help='Leave blank to use OPENAI_API_KEY from your shell.')
    exa_key = st.text_input('Exa API key', type='password', help='Leave blank to use EXA_API_KEY from your shell.')
    model = st.text_input('OpenAI model', value='gpt-5')
    st.caption('Keys remain in this session and are never included in downloads. Your brief and retrieved sources are sent to OpenAI and Exa.')
    st.divider()
    st.subheader('The workflow')
    st.write('1. Discover companies\n2. Identify contacts\n3. Research context\n4. Draft emails')
    st.caption('Drafts only. Review sources and email addresses before using them.')

with st.form('brief'):
    st.subheader('Define your outreach')
    targeting = st.text_area('Who do you want to reach?', max_chars=4000,
        placeholder='Example: B2B SaaS companies in India with 20–100 employees, expanding their sales teams.')
    offering = st.text_area('What do you offer?', max_chars=4000,
        placeholder='Describe your product, who it helps, and the concrete problem it solves.')
    left, right = st.columns(2)
    count = left.slider('Number of companies', 1, 10, 3)
    style = right.selectbox('Email style', ['Professional', 'Casual', 'Cold', 'Consultative'])
    allow_inferred = st.checkbox('Include inferred business emails', value=False,
        help='Guessed addresses are labeled inferred and are not verified or deliverability-checked.')
    start = st.form_submit_button('Start Outreach', type='primary')

api_key = openai_key.strip() or os.getenv('OPENAI_API_KEY', '')
search_key = exa_key.strip() or os.getenv('EXA_API_KEY', '')
if start:
    if not targeting.strip() or not offering.strip():
        st.error('Add both a targeting description and your offering.')
    elif not api_key or not search_key or not model.strip():
        st.error('Enter both API keys and an OpenAI model in the sidebar, or set the keys in your shell.')
    else:
        st.session_state.run = {'config': {'targeting': targeting.strip(), 'offering': offering.strip(),
            'count': count, 'style': style, 'allow_inferred': allow_inferred, 'model': model.strip()}}
        st.session_state.execute = True

state = st.session_state.get('run')
if state and not state.get('complete') and not st.session_state.get('execute'):
    if st.button('Resume unfinished stages'):
        st.session_state.execute = True

if st.session_state.pop('execute', False):
    if not api_key or not search_key:
        st.error('Enter both API keys to resume.')
    else:
        meter = st.progress(0, text='Starting outreach')
        with st.status('Working on your outreach', expanded=True) as status:
            current_stage = [None]
            def update(value, stage, detail):
                meter.progress(value, text=f'{stage} — {detail}')
                if stage != current_stage[0]:
                    st.write(stage)
                    current_stage[0] = stage
                status.update(label=f'{stage} — {detail}')
            workflow = None
            try:
                workflow = Workflow(api_key, search_key, state['config']['model'])
                workflow.run(state, update)
                status.update(label='Outreach ready for review', state='complete', expanded=False)
            except StageError as exc:
                status.update(label='Run paused — completed work is saved in this session', state='error')
                st.error(str(exc))
            except Exception:
                status.update(label='Run paused', state='error')
                st.error('An unexpected error interrupted this run. Completed work is retained; resume to retry.')
            finally:
                if workflow:
                    workflow.close()
        if not state.get('complete'):
            if st.button('Resume unfinished stages', key='retry_now'):
                st.session_state.execute = True
                st.rerun()


def sources_ui(ids, sources):
    for source in referenced(ids, sources):
        st.link_button(source['title'] or source['url'], source['url'])


if state and state.get('companies'):
    st.divider()
    st.header('Your outreach workspace')
    st.caption(f"{len(state['companies'])} of {state['config']['count']} requested companies · {state['config']['style']} style · "
               + ('Complete' if state.get('complete') else 'Partial results'))
    if len(state['companies']) < state['config']['count']:
        st.info('Fewer companies matched the available evidence. Broaden your targeting for more results.')
    left, right = st.columns(2)
    left.download_button('Download research & emails', markdown_export(state), 'outreach.md', 'text/markdown')
    right.download_button('Download complete JSON', json.dumps(state, indent=2), 'outreach.json', 'application/json')
    for index, company in enumerate(state['companies']):
        st.divider()
        st.subheader(company['name'])
        st.write(company['fit'])
        st.link_button('Company website', company['website'])
        contacts_tab, research_tab, emails_tab = st.tabs(['Contacts', 'Research', 'Email drafts'])
        with contacts_tab:
            if not company.get('contacts'):
                st.info('No supported contacts yet. No names or email addresses have been invented.')
            for contact in company.get('contacts', []):
                st.write(f"**{contact['name']}** · {contact['role']}")
                st.text(f"{contact['email'] or 'Email unavailable'} — {contact['email_status']}")
                with st.expander(f"Sources for {contact['name']}"):
                    sources_ui(contact['source_ids'], company['contact_sources'])
            st.caption('Published means found in retrieved text; it does not confirm current role, ownership, or deliverability.')
        with research_tab:
            research = company.get('research')
            if not research:
                st.info('Research has not completed yet.')
            else:
                for insight in research['insights']:
                    st.write(insight['finding'])
                    st.caption(insight['relevance'])
                    sources_ui(insight['source_ids'], company['research_sources'])
                if research['limitations']:
                    st.info(research['limitations'])
        with emails_tab:
            for j, draft in enumerate(company.get('drafts', [])):
                st.write(f"**To {draft['contact']['name']}**")
                text = f"Subject: {draft['subject']}\n\n{draft['body']}"
                st.code(text, language=None, wrap_lines=True)
                st.download_button('Download this email', text, f'email-{index + 1}-{j + 1}.txt',
                    'text/plain', key=f'email-{index}-{j}')
            if not company.get('drafts'):
                st.info('Drafts appear here after contacts and research are ready.')
    if st.button('Clear this run'):
        del st.session_state.run
        st.rerun()
else:
    st.divider()
    st.subheader('A useful email starts with context')
    st.write('Describe a specific audience and offering. Your results will include company fit, decision makers, source-backed insights, and individual email drafts.')
