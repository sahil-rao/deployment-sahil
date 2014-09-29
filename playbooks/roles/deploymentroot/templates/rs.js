config = {_id: "{{ silo_name }}" , members: [
                          {_id: 0, host: "{{ groups['just_created_mongodb'][0] }}"},
                          {_id: 1, host: "{{ groups['just_created_mongodb'][1] }}"},
                          {_id: 2, host: "{{ groups['just_created_arbiter'][0] }}", arbiterOnly : true}]
}

rs.initiate(config)
