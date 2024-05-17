#!/usr/bin/env python3

import logging, grpc

from .grpc_stubs import platform_iface_pb2, platform_iface_pb2_grpc


class platform_iface:
    def __init__(
            self, 
            plt_uri="localhost:50053", 
        ):
        
        self.plt_uri = plt_uri

    def make_request(self, stub_call, request):
        try:
            with grpc.insecure_channel(self.plt_uri) as channel:
                stub = platform_iface_pb2_grpc.platformIfaceStub(channel)
                response = getattr(stub, stub_call)(request)
                return response
        except Exception as e:
            logging.warning("Error making platform iface request: " + str(e))
            return None
    
    def process_response(self, response, response_field):
        if response is None:
            logging.warning("Error processing " + str(response_field) + " response: " + str(response))
            return None
        if not response.response_header.success:
            logging.warning("Error processing " + str(response_field) + " response: " + str(response.response_header.message))
            return None
        result = list(getattr(response, response_field))
        if isinstance(result, list) and len(result) == 1:
            return result[0]
        return result


    def get_di(self, di):
        if type(di) == int:
            di = [di]
        elif type(di) != list:
            logging.error("Invalid type for digital input: " + str(type(di)))
            return None
        
        # Above section is to facilitate the following:
        # get_di(1)
        # get_di([1,4,2])

        result = self.make_request('getDI', platform_iface_pb2.getDIRequest(di=di))
        return self.process_response(result, 'di')
    

    ####

    def get_ai(self, ai):
        if type(ai) == int:
            ai = [ai]
        elif type(ai) != list:
            logging.error("Invalid type for analog input: " + str(type(ai)))
            return None
        
        # Above section is to facilitate the following:
        # get_ai(1)
        # get_ai([1,4,2])

        result = self.make_request('getAI', platform_iface_pb2.getAIRequest(ai=ai))
        return self.process_response(result, 'ai')

        
    def get_do(self, do):

        if type(do) == int:
            do = [do]
        elif type(do) != list:
            logging.error("Invalid type for digital output: " + str(type(do)))
            return None
        
        # Above section is to facilitate the following:
        # get_do(1) 
        # get_do([1,4,2])

        result = self.make_request('getDO', platform_iface_pb2.getDORequest(do=do))
        return self.process_response(result, 'do')
    

    def set_do(self, do, value):

        if type(do) == int:
            do = [do]
        elif type(do) != list:
            logging.error("Invalid type for digital output: " + str(type(do)))
            return None
        
        if type(value) == int:
            value = [value]
        if type(value) == bool:
            value = [value]
        elif type(value) != list:
            logging.error("Invalid type for digital output value: " + str(type(value)))
            return None
        
        if len(do) != len(value):
            if len(value) == 1:
                value = [value[0]] * len(do)
            else:
                logging.error("Digital output and value lists are not the same length.")
                return None
            
        # Above section is to facilitate the following:
        # set_do(1, 1) => [1],[1]
        # set_do([1,4,2], 0) => [1,4,2], [0,0,0]
        # set_do([1,4,2], [0,1,0]) => [1,4,2], [0,1,0]
        
        result = self.make_request('setDO', platform_iface_pb2.setDORequest(do=do, value=value))
        return self.process_response(result, 'do')
    

    def schedule_do(self, do, value, time):
            
            if type(do) == int:
                do = [do]
            elif type(do) != list:
                logging.error("Invalid type for digital output: " + str(type(do)))
                return None
            
            if type(value) == int:
                value = [value]
            elif type(value) != list:
                logging.error("Invalid type for digital output value: " + str(type(value)))
                return None
            
            if len(do) != len(value):
                if len(value) == 1:
                    value = [value[0]] * len(do)
                else:
                    logging.error("Digital output and value lists are not the same length.")
                    return None
                
            # Above section is to facilitate the following:
            # schedule_do(1, 1, 1) => [1],[1],1
            # schedule_do([1,4,2], 0, 1) => [1,4,2], [0,0,0], 1
            # schedule_do([1,4,2], [0,1,0], 1) => [1,4,2], [0,1,0], 1
            
            result = self.make_request('scheduleDO', platform_iface_pb2.scheduleDORequest(do=do, value=value, time_secs=time))
            return self.process_response(result, 'do')
    

    ####

    def get_ao(self, ao):

        if type(ao) == int:
            ao = [ao]
        elif type(ao) != list:
            logging.error("Invalid type for analog output: " + str(type(ao)))
            return None
        
        # Above section is to facilitate the following:
        # get_ao(1) 
        # get_ao([1,4,2])

        result = self.make_request('getAO', platform_iface_pb2.getAORequest(ao=ao))
        return self.process_response(result, 'ao')


    def set_ao(self, ao, value):
        if type(ao) == int:
            ao = [ao]
        elif type(ao) != list:
            logging.error("Invalid type for analog output: " + str(type(ao)))
            return None
        
        if type(value) == int:
            value = [value]
        elif type(value) != list:
            logging.error("Invalid type for analog output value: " + str(type(value)))
            return None
        
        if len(ao) != len(value):
            if len(value) == 1:
                value = [value[0]] * len(ao)
            else:
                logging.error("Digital output and value lists are not the same length.")
                return None
            
        # Above section is to facilitate the following:
        # set_ao(1, 1) => [1],[1]
        # set_ao([1,4,2], 0) => [1,4,2], [0,0,0]
        # set_ao([1,4,2], [0,1,0]) => [1,4,2], [0,1,0]
        
        result = self.make_request('setAO', platform_iface_pb2.setAORequest(ao=ao, value=value))
        return self.process_response(result, 'ao')


    def schedule_ao(self, ao, value, time):

        if type(ao) == int:
            ao = [ao]
        elif type(ao) != list:
            logging.error("Invalid type for analog output: " + str(type(ao)))
            return None
        
        if type(value) == int:
            value = [value]
        elif type(value) != list:
            logging.error("Invalid type for analog output value: " + str(type(value)))
            return None
        
        if len(ao) != len(value):
            if len(value) == 1:
                value = [value[0]] * len(ao)
            else:
                logging.error("Digital output and value lists are not the same length.")
                return None
            
        # Above section is to facilitate the following:
        # schedule_ao(1, 1, 1) => [1],[1],1
        # schedule_ao([1,4,2], 0, 1) => [1,4,2], [0,0,0], 1
        # schedule_ao([1,4,2], [0,1,0], 1) => [1,4,2], [0,1,0], 1
        
        result = self.make_request('scheduleAO', platform_iface_pb2.scheduleAORequest(ao=ao, value=value, time_secs=time))
        return self.process_response(result, 'ao')
    



if __name__ == "__main__":
    P_IFACE = platform_iface()
    print(P_IFACE.set_ao([3,0,1], 1))