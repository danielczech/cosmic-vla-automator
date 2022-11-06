import redis
from interface import Interface
from logger import log

class Automator(object):
    """Automation for commensal observing with the COSMIC system at the VLA.
    This process coordinates and automates commensal observing and SETI 
    search processing at a high level.

    Two observational modes are to be supported: Stop-and-stare (where fixed 
    coordinates in RA and Dec are observed) and VLASS-style observing 
    (scanning across the sky).

    Based on the following knowledge:

    - The current state of the telescope
    - The current state of the COSMIC recording/processing system
    - The observing (processing and recording) behaviour desired by operators

    the automator is to determine what instructions (if any) to deliver to the 
    processing nodes. 

    TODO: implement retries for certain operations
    TODO: implement slack notifications for operational stages

    """

    def __init__(self, redis_endpoint, antenna_key, instances, daq_domain, 
                 duration):
        """Initialise automator.

        Args:
            redis_endpoint (str): Redis endpoint (of the form 
            <host IP address>:<port>)
        
        Returns:
            None
        """
        log.info('Starting Automator:\n'
                 'Redis endpoint: {}\n'.format(redis_endpoint))
        redis_host, redis_port = redis_endpoint.split(':')
        self.r = redis.StrictRedis(host=redis_host, 
                                              port=redis_port, 
                                              decode_responses=True)
        self.antenna_hash_key = antenna_key
        self.instances = instances
        self.daq_domain = daq_domain
        self.duration = duration

    def start(self):
        """Start the automator. Actions to be taken depend on the incoming 
        observational stage messages on the appropriate Redis channel. 
        """   
        
        utils.alert('Starting up...')

        ps = self.r.pubsub(ignore_subscribe_messages=True)
        
        # Check if we are already on source:
        tel_state_on_startup = Interface.telescope_state(
            antenna_hash=self.antenna_hash_key)
        if tel_state_on_startup == 'on_source':
            # If we are on source, potentially initiate recording for any 
            # available processing nodes 
            rec_instances = Interface.record_conditional(self.daq_domain, 
                                         self.instances, 
                                         self.duration)                 
            # Listen to each hashpipe instance hash to monitor recording:

        else:
            utils.alert('Telescope in state: {}'.format(tel_state_on_startup))
            rec_instances = []

        # Listen to antenna station key and compare allocated antennas with 
        # on-source antennas to determine recording readiness 
        ps.subscribe('__keyspace@0__:{}').format(self.antenna_hash_key)
        for updated_key in ps.listen():
            if updated_key['data'] == 'set':
                # Check what was updated:
                channel = updated_key['channel'].split(':')[1]
                # If the antenna flags have been updated, check if the telescope 
                # has transitioned between off_source and on source:
                if channel == self.antenna_hash_key:
                    tel_state = Interface.telescope_state(antenna_hash=self.antenna_hash_key)
                    # Stop recording for all instances if telescope moves off 
                    # source during recording:
                    if tel_state == 'off_source':
                        daq_states = self.daq_states(daq_domain, instances)
                        if len(daq_states['recording']) > 0:
                            Interface.stop_recording()
                            # Unsubscribe from any recording keyspace notifications:

                            # Potentially start processing here:

                    # Potentially start recording if the telescope moves on source:
                    elif tel_state == 'on_source':
                        rec_instances = Interface.record_conditional(self.daq_domain, 
                                                     self.instances, 
                                                     self.duration)                 
                        # Listen to each hashpipe instance hash to monitor recording:

            # If we stop processing, check if we should start postprocessing

            # If we stop postprocessing, check if we should start recording

