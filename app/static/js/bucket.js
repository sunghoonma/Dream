/**
 * @author Ma Sunghoon
 */

function TasksViewModel(username) {
    var self = this;
    self.tasksURI = '/api/users/'+username+'/buckets';
    self.tasks = ko.observableArray();
    self.bucketDecade = ko.observableArray();
    self.bucketYearly = ko.observableArray();
    self.bucketMonthly = ko.observableArray();
    self.bucketWeekly = ko.observableArray();

    self.ajax = function(uri, method, data) {
        var request = {
            url: uri,
            type: method,
            contentType: "application/json",
            accepts: "application/json",
            cache: false,
            dataType: 'json',
            data: JSON.stringify(data),
            error: function(jqXHR) {
                console.log("ajax error " + jqXHR.status);
            }
        };
        return $.ajax(request);
    }
    
    self.updateTask = function(task, newTask) {
    	t = 'bucket'+capitalise(newTask.scope);
		for (var j in self[t]()){
			if (self[t]()[j].uri() == task.uri()){
		        self[t]()[j].uri(newTask.uri);
		        self[t]()[j].title(newTask.title);
		       	self[t]()[j].description(newTask.description);
		        self[t]()[j].done(newTask.is_live);
				self[t]()[j].private(newTask.is_private);
				self[t]()[j].deadline(newTask.deadline);
				self[t]()[j].scope(newTask.scope);
				self[t]()[j].range(newTask.range);
			}
		}
        var i = self.tasks.indexOf(task);
        self.tasks()[i].uri(newTask.uri);
        self.tasks()[i].title(newTask.title);
       	self.tasks()[i].description(newTask.description);
        self.tasks()[i].done(newTask.is_live);
		self.tasks()[i].private(newTask.is_private);
		self.tasks()[i].deadline(newTask.deadline);
		self.tasks()[i].scope(newTask.scope);
		self.tasks()[i].range(newTask.range);
		
    }

   self.beginAdd = function() {
	   addTaskViewModel.setClear();
       $('#addBucket').modal('show');
   }
   self.add = function(task) {
       self.ajax(self.tasksURI, 'POST', task).done(function(data) {
    	   self.tasks.push({
               uri: ko.observable(data.bucket.uri),
               title: ko.observable(data.bucket.title),
               description: ko.observable(data.bucket.description),
			   done: ko.observable(data.bucket.is_live),
               private: ko.observable(data.bucket.is_private),
			   deadline: ko.observable(data.bucket.deadline.substr(0,10)),
			   detailUri: ko.observable('/user/'+username+'/bucket/'+data.bucket.id)
           });
       });
   	}
	self.todoADD = function(data) {
		self.ajax('/api/buckets/'+bucketID, 'POST', data).done(function(res) {
			self.todos.push({
                todotitle: ko.observable(res.bucket.title),
                tododone: ko.observable(res.bucket.is_live),
                tododeadline: ko.observable(res.bucket.deadline)
			});
			// self.updateTask(task, res.todo);
		});
	}
    self.beginEdit = function(task) {
        editTaskViewModel.setTask(task.id());
        $('#editBucket').modal('show');
    }
    self.edit = function(task, data) {
        self.ajax(task.uri(), 'PUT', data).done(function(res) {
            self.updateTask(task, res.bucket);
        });
    }
	 self.remove = function(task) {
	     self.ajax(task.uri(), 'DELETE').done(function() {
	         t = 'bucket'+capitalise(task.scope());
	 		 for (var j in self[t]()){
	 			if (self[t]()[j].uri() == task.uri()){
	 				self[t].remove(self[t]()[j])
	 			}
	 		}
	 		self.tasks.remove(task);
	     });
	 }
    self.delFromList = function(task) {
    	self.ajax(task.uri(), 'PUT', { is_live: 9 }).done(function(res) {
    		self.updateTask(task. res.bucket);
    	});
    }
    self.markInProgress = function(task) {
        self.ajax(task.uri(), 'PUT', { is_live: 0 }).done(function(res) {
            self.updateTask(task, res.bucket);
        });
    }
    self.markDone = function(task) {
        self.ajax(task.uri(), 'PUT', { is_live: 1 }).done(function(res) {
            self.updateTask(task, res.bucket);
        });
    }
    self.init = function() {
        self.ajax(self.tasksURI, 'GET').done(function(data) {
            for (var i = 0; i < data.buckets.length; i++) {
            	if (data.buckets[i].scope != 'TODO'){
            		t = 'bucket'+capitalise(data.buckets[i].scope);
            		self[t].push({
            			uri: ko.observable(data.buckets[i].uri),
	                    id: ko.observable(data.buckets[i].id),
	                    title: ko.observable(data.buckets[i].title),
	                   	description: ko.observable(data.buckets[i].description),
	                    done: ko.observable(data.buckets[i].is_live),
						private: ko.observable(data.buckets[i].is_private),
						deadline: ko.observable(data.buckets[i].deadline),
						scope: ko.observable(data.buckets[i].scope),
						range: ko.observable(data.buckets[i].range),
						detailUri: ko.observable('/user/'+username+'/bucket/'+data.buckets[i].id)
	            	});
	                self.tasks.push({
	                    uri: ko.observable(data.buckets[i].uri),
	                    id: ko.observable(data.buckets[i].id),
	                    title: ko.observable(data.buckets[i].title),
	                   	description: ko.observable(data.buckets[i].description),
	                    done: ko.observable(data.buckets[i].is_live),
						private: ko.observable(data.buckets[i].is_private),
						deadline: ko.observable(data.buckets[i].deadline),
						scope: ko.observable(data.buckets[i].scope),
						range: ko.observable(data.buckets[i].range),
						detailUri: ko.observable('/user/'+username+'/bucket/'+data.buckets[i].id)
	                });
            	}
            }
        });
    }

    self.init();
}
var sampleProductCategories = new Array();
function AddTaskViewModel() {
    var self = this;
    
    self.ajax = function(uri, method, data) {
        var request = {
            url: uri,
            type: method,
            contentType: "application/json",
            accepts: "application/json",
            cache: false,
            dataType: 'json',
            data: JSON.stringify(data),
            async: false,
            error: function(jqXHR) {
                console.log("ajax error " + jqXHR.status);
            }
        };
        return $.ajax(request);
    };
   
    self.ajax('/api/getUserDday','GET').done(function(res) {
        sampleProductCategories = res.data;
    });
    
    self.title = ko.observable();
    self.description = ko.observable();
	self.private = ko.observable();
	self.done = ko.observable();
	self.due = ko.observable();
	
	self.category = ko.observable();
    self.product = ko.observable();
    self.dueDate = ko.observable();
	
    self.addTask = function() {
    	$('#addBucket').modal('hide');
    	tasksViewModel.add({
    		title: self.title(),
    		description: self.description(),
    		is_private: self.private(),
    		is_live: self.done(),
//    		deadline: self.due(),
    		scope: self.category().name,
    		range: self.product().range,
    		deadline: self.product().dueDate
        });
    	self.setClear();
    }	
    	
    self.setClear = function(){
        self.title("");
        self.description("");
		self.private("");
		self.done("");
		self.due("");
    }
}

function EditTaskViewModel() {
    var self = this;
    self.title = ko.observable();
    self.description = ko.observable();
    self.private = ko.observable();
    self.done = ko.observable();
    self.deadline = ko.observable();

    self.inputTodoTitle = ko.observable();
    self.inputTodoDue = ko.observable();
    
    self.todos = ko.observableArray();

    self.setTask = function(bucketID) {
    	self.todos.removeAll();
    	tasksViewModel.ajax('/api/buckets/'+bucketID, 'GET').done(function(data){
            self.title(data.bucket.title);
            self.description(data.bucket.description);
            self.private(data.bucket.private);
            self.done(data.bucket.done);
            self.deadline(data.bucket.deadline);
            for (var i=0; i<data.todo.length; i++){
                self.todos.push({
                    todotitle: ko.observable(data.todo[i].title),
                    tododone: ko.observable(data.todo[i].is_live),
                    tododeadline: ko.observable(data.todo[i].deadline)
                });
            }
        });
    }
    
	self.addTodo = function(){
		tasksViewModel.todoADD({
			title: self.inputTodoTitle(),
			level: '00000100',
			parent_id: bucketID,
			scope: 'TODO_N'
		});
	}

    self.editTask = function() {
        $('#editBucket').modal('hide');
        tasksViewModel.edit(self.task, {
            title: self.title(),
            description: self.description() ,
            is_private: self.private(),
            is_live: self.done(),
            deadline: self.deadline()
        });
    }
}

function capitalise(string){
	return string.charAt(0).toUpperCase() + string.slice(1).toLowerCase();
}