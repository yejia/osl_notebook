


class Router(object):
    """A router to control all database operations on models"""
    
    #so far, django has only hint for instance. So with no hint for field
    #need to do something special in the project code when getting form field 
    #choices, such as for tags 
  

    def get_db(self, model, **hints):
        if hasattr(model, 'owner_name'):
            return model.owner_name 
        elif hints.get('instance') and hasattr(hints['instance'], 'owner_name'):
            return hints['instance'].owner_name
        else:            
            return 'default'


    def db_for_read(self, model, **hints):  
        return self.get_db(model, **hints)

  
    def db_for_write(self, model, **hints):
        return self.get_db(model, **hints)
