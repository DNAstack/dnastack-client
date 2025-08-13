from typing import TypeVar

from dnastack.client.workbench.ewes.client import EWesClient
from dnastack.client.workbench.ewes.models import ExtendedRunListOptions
from dnastack.common.environments import flag
from tests.util.exam_helper_for_workbench import BaseWorkbenchTestCase

T = TypeVar('T')


class TestClient(BaseWorkbenchTestCase):
    _ewes_tests_enabled = flag('E2E_EWES_TESTS_ENABLED')

    def setUp(self):
        super(TestClient, self).setUp()

        if not self._ewes_tests_enabled:
            self.skipTest('Tests disabled... Set E2E_EWES_TESTS_ENABLED to true to enable.')

    def test_submit_run(self):
        submitted_run = self.submit_hello_world_workflow_run()
        expected_states = ['QUEUED', 'INITIALIZING', 'RUNNING']
        self.assertTrue(submitted_run.state in expected_states, f'Expected any state from {expected_states}. '
                                                                f'Instead found {submitted_run.state}.')

    def test_submit_batch(self):
        submitted_batch = self.submit_hello_world_workflow_batch()
        expected_states = ['QUEUED', 'INITIALIZING', 'RUNNING']
        self.assertEqual(len(submitted_batch.runs), 2, 'Expected exactly two runs in a batch.')
        self.assertTrue(submitted_batch.runs[0].state in expected_states,
                        f'Expected any state from {expected_states}. Instead found {submitted_batch.runs[0].state}.')

    def test_get_run(self):
        ewes_client: EWesClient = self.get_ewes_client()
        submitted_run = self.submit_hello_world_workflow_run()

        run = ewes_client.get_run(submitted_run.run_id)
        self.assertEqual(run.run_id, submitted_run.run_id, 'Expected IDs to be same.')
        self.assertEqual(run.request.workflow_params.get('test.hello.name'), 'foo',
                         'Expected workflow param to be equal to \'foo\'.')

    def test_list_runs(self):
        ewes_client: EWesClient = self.get_ewes_client()
        self.submit_hello_world_workflow_batch()

        runs = list(ewes_client.list_runs(list_options=None, max_results=None))
        self.assertGreater(len(runs), 1, 'Expected at least two runs.')

        runs = list(ewes_client.list_runs(list_options=None, max_results=1))
        self.assertEqual(len(runs), 1, 'Expected exactly one run.')

        runs = list(ewes_client.list_runs(list_options=ExtendedRunListOptions(engine_id=self.execution_engine.id),
                                          max_results=None))
        self.assertGreater(len(runs), 1, 'Expected at least two runs.')

        runs = list(ewes_client.list_runs(list_options=ExtendedRunListOptions(engine_id='foo'),
                                          max_results=None))
        self.assertEqual(len(runs), 0, 'Expected exactly zero runs.')

    def test_list_run_events(self):
        """Test listing run events and verifying discriminated union deserialization."""
        ewes_client: EWesClient = self.get_ewes_client()
        submitted_run = self.submit_hello_world_workflow_run()

        # Test list_events method
        run_events = ewes_client.list_events(submitted_run.run_id)
        self.assertIsNotNone(run_events, 'Expected ExtendedRunEvents object')
        self.assertIsNotNone(run_events.events, 'Expected events list to be present')
        self.assertGreater(len(run_events.events), 0, 'Expected at least one event')

        # Test first event (should be RUN_SUBMITTED)
        first_event = run_events.events[0]
        from dnastack.client.workbench.ewes.models import EventType, RunSubmittedMetadata
        
        self.assertEqual(first_event.event_type, EventType.RUN_SUBMITTED,
                         'Expected first event to be RUN_SUBMITTED')
        
        # Test discriminated union deserialization
        self.assertIsInstance(first_event.metadata, RunSubmittedMetadata,
                              'Expected RunSubmittedMetadata for RUN_SUBMITTED event')
        
        # Test discriminator field consistency
        self.assertEqual(first_event.event_type, first_event.metadata.event_type,
                         'Expected event_type to match between event and metadata')

        # Test that metadata fields are properly typed and accessible
        self.assertIsNotNone(first_event.id, 'Expected event to have ID')
        self.assertIsNotNone(first_event.created_at, 'Expected event to have created_at timestamp')
        
        # Test optional fields behavior
        submitted_by = first_event.metadata.submitted_by
        workflow_name = first_event.metadata.workflow_name
        
        # These might be None depending on the actual event data
        # Just verify they're accessible without AttributeError
        self.assertTrue(submitted_by is None or isinstance(submitted_by, str),
                        'submitted_by should be None or string')
        self.assertTrue(workflow_name is None or isinstance(workflow_name, str),
                        'workflow_name should be None or string')

        # Test serialization roundtrip for all events
        for i, event in enumerate(run_events.events):
            try:
                # Convert to dict and back
                event_dict = event.dict()
                from dnastack.client.workbench.ewes.models import RunEvent
                reconstructed_event = RunEvent(**event_dict)
                
                self.assertEqual(event.id, reconstructed_event.id,
                                 f'Event {i}: ID mismatch after serialization roundtrip')
                self.assertEqual(event.event_type, reconstructed_event.event_type,
                                 f'Event {i}: event_type mismatch after serialization roundtrip')
                self.assertEqual(type(event.metadata), type(reconstructed_event.metadata),
                                 f'Event {i}: metadata type mismatch after serialization roundtrip')
                
            except Exception as e:
                self.fail(f'Serialization roundtrip failed for event {i}: {e}')

        print(f'Successfully tested {len(run_events.events)} events for run {submitted_run.run_id}')
