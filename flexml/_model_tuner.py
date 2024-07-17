from typing import Union, Optional
import numpy as np
import pandas as pd
import optuna

from sklearn.model_selection import GridSearchCV, RandomizedSearchCV
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score

from flexml.logger.logger import get_logger


class ModelTuner:
    """
    Implements hyperparameter tuning on the machine learning models with the desired tuning method from the following:

    * 'grid_search' for GridSearchCV (https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GridSearchCV.html)
        Note that GridSearch optimization may take too long to finish since It tries all the possible combinations of the parameters

    * 'randomized_search' for RandomizedSearchCV (https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.RandomizedSearchCV.html)
            
    * 'optuna' for Optuna (https://optuna.readthedocs.io/en/stable/)

    Parameters
    ----------
    ml_problem_type : str
        The type of the machine learning problem. It can be one of the following:
        
        * 'Classification' for classification problems
        
        * 'Regression' for regression problems

    X_train : pd.DataFrame
        The training set features
    
    X_test : pd.DataFrame
        The test set features

    y_train : pd.DataFrame
        The training set target values

    y_test : pd.DataFrame
        The test set target values
    """
    def __init__(self, 
                 ml_problem_type: str,
                 X_train: pd.DataFrame, 
                 X_test: pd.DataFrame, 
                 y_train: pd.DataFrame, 
                 y_test: pd.DataFrame,
                 logging_to_file: bool = True):
        self.ml_problem_type = ml_problem_type.lower().capitalize() # Fix ml_problem_type's format in just case, It should be in the following format: 'Example'
        self.X_train = X_train
        self.X_test = X_test
        self.y_train = y_train
        self.y_test = y_test

        self.X = pd.concat([self.X_train, self.X_test], axis=0)
        self.y = pd.concat([self.y_train, self.y_test], axis=0)

        self.logger = get_logger(__name__, logging_to_file)

    def _param_grid_validator(self,
                        param_grid: dict):
        """
        This method is used to validate the param_grid dictionary for the model. Also It changes the size of the param_grid If the user wants to have a quick optimization.

        Parameters
        ----------
        model : object
            The model object that will be tuned.

        param_grid : dict
            The dictionary that contains the hyperparameters and their possible values.

        # TODO
        optimization_size : str, optional (default="quick")
            The size of the optimization. It can be 'quick' or 'wide'. The default is "quick".

            * If It's 'wide', whole the param_grid that defined in flexml/config/ml_models.py will be used for the optimization

            * If It's 'quick', only the half of the param_grid that defined in flexml/config/ml_models.py will be used for the optimization
                
                -> This is used to decrease the optimization time by using less hyperparameters, but It may not give the best results compared to 'wide' since 'wide' uses more hyperparameters
                
                -> Also, half of the param_grid will be selected randomly, so the results may change in each run
        """
        # IN PROGRESS
        return param_grid
    
    def _model_evaluator(self,
                         model: object,
                         eval_metric: str):
        """
        Evaluates the model with the given evaluation metric by using the test set

        Parameters
        ----------
        model : object
            The model object that will be evaluated.

        eval_metric : str
            The evaluation metric that will be used to evaluate the model. It can be one of the following:
            
            * 'r2' for R^2 score
            
            * 'mae' for Mean Absolute Error
            
            * 'mse' for Mean Squared Error
            
            * 'accuracy' for Accuracy
            
            * 'precision' for Precision
            
            * 'recall' for Recall
            
            * 'f1' for F1 score
        """
        
        match eval_metric.lower():
            case 'r2':
                return r2_score(self.y_test, model.predict(self.X_test))
            case 'mae':
                return mean_absolute_error(self.y_test, model.predict(self.X_test))
            case 'mse':
                return mean_squared_error(self.y_test, model.predict(self.X_test))
            case 'accuracy':
                return accuracy_score(self.y_test, model.predict(self.X_test))
            case 'precision':
                return precision_score(self.y_test, model.predict(self.X_test))
            case 'recall':
                return recall_score(self.y_test, model.predict(self.X_test))
            case 'f1':
                return f1_score(self.y_test, model.predict(self.X_test))
            case _:
                error_msg = "Error while evaluating the current model during the model tuning process. The eval_metric should be one of the following: 'r2', 'mae', 'mse', 'accuracy', 'precision', 'recall', 'f1'"
                self.logger.error(error_msg)
                raise ValueError(error_msg)
            
    def grid_search(self,
                    model: object,
                    param_grid: dict,
                    eval_metric: str,
                    cv: int = 3,
                    n_jobs: int = -1) -> Optional[dict]:
        """
        Implements grid search hyperparameter optimization on the giveen machine learning model

        Parameters
        ----------
        model : object
            The model object that will be tuned.

        param_grid : dict
            The dictionary that contains the hyperparameters and their possible values.

        eval_metric : str
            The evaluation metric that will be used to evaluate the model. It can be one of the following:
            
            * 'r2' for R^2 score
            
            * 'mae' for Mean Absolute Error
            
            * 'mse' for Mean Squared Error
            
            * 'accuracy' for Accuracy
            
            * 'precision' for Precision
            
            * 'recall' for Recall
            
            * 'f1' for F1 score

        cv : int, optional (default=3)
            The number of cross-validation splits. The default is 3.

        n_jobs : int, optional (default=-1)
            The number of parallel jobs to run. The default is -1.

        Returns
        -------
        model_stats: dict
            Dictionary including tuning information and model:

            * 'tuning_method': The tuning method that is used for the optimization
            
            * 'tuning_param_grid': The hyperparameter grid that is used for the optimization
            
            * 'cv': The number of cross-validation splits
            
            * 'n_jobs': The number of parallel jobs to run
            
            * 'tuned_model': The tuned model object
            
            * 'tuned_model_score': The evaluation metric score of the tuned model
            
            * 'tuned_model_evaluation_metric': The evaluation metric that is used to evaluate the tuned model
        """
        model_stats = {
            "tuning_method": "GridSearchCV",
            "tuning_param_grid": param_grid,
            "cv": cv,
            "n_jobs": n_jobs,
            "tuned_model": None,
            "tuned_model_score": None,
            "tuned_model_evaluation_metric": None
        }
        
        try:
            search_result = GridSearchCV(model, param_grid, scoring=eval_metric, cv=cv, n_jobs=n_jobs, verbose=1).fit(self.X, self.y)

            model_stats['tuned_model'] = search_result.best_estimator_
            model_stats['tuned_model_score'] = self._model_evaluator(search_result.best_estimator_, eval_metric)
            model_stats['tuned_model_evaluation_metric'] = eval_metric
            return model_stats
        
        except Exception as e:
            self.logger.error(f"Error while tuning the model with GridSearchCV, Error: {e}")
            return None
    
    def random_search(self,
                      model: object,
                      param_grid: dict,
                      eval_metric: str,
                      n_trials: int = 10,
                      cv: int = 3,
                      n_jobs: int = -1) -> Optional[dict]:
        """
        Implements random search hyperparameter optimization on the giveen machine learning model

        Parameters
        ----------
        model : object
            The model object that will be tuned.

        param_grid : dict
            The dictionary that contains the hyperparameters and their possible values.

        eval_metric : str
            The evaluation metric that will be used to evaluate the model. It can be one of the following:
            
            * 'r2' for R^2 score
            
            * 'mae' for Mean Absolute Error
            
            * 'mse' for Mean Squared Error
            
            * 'accuracy' for Accuracy
            
            * 'precision' for Precision
            
            * 'recall' for Recall
            
            * 'f1' for F1 score

        n_trials : int, optional (default=10)
            The number of trials. The default is 10.

        cv : int, optional (default=3)
            The number of cross-validation splits. The default is 3.

        n_jobs : int, optional (default=-1)
            The number of parallel jobs to run. The default is -1.

        # TODO
        optimization_size : str, optional (default="quick")
            The size of the optimization. It can be 'quick' or 'wide'. The default is "quick".

            * If It's 'wide', whole the param_grid that defined in flexml/config/ml_models.py will be used for the optimization

            * If It's 'quick', only the half of the param_grid that defined in flexml/config/ml_models.py will be used for the optimization
                
                -> This is used to decrease the optimization time by using less hyperparameters, but It may not give the best results compared to 'wide' since 'wide' uses more hyperparameters
                
                -> Also, half of the param_grid will be selected randomly, so the results may change in each run
        
        Returns
        -------
        model_stats: dict
            Dictionary including tuning information and model:

            * 'tuning_method': The tuning method that is used for the optimization
            
            * 'tuning_param_grid': The hyperparameter grid that is used for the optimization
            
            * 'cv': The number of cross-validation splits
            
            * 'n_jobs': The number of parallel jobs to run
            
            * 'tuned_model': The tuned model object
            
            * 'tuned_model_score': The evaluation metric score of the tuned model
            
            * 'tuned_model_evaluation_metric': The evaluation metric that is used to evaluate the tuned model
        """
        model_stats = {
            "tuning_method": "RandomizedSearchCV",
            "tuning_param_grid": param_grid,
            "cv": cv,
            "n_jobs": n_jobs,
            "tuned_model": None,
            "tuned_model_score": None,
            "tuned_model_evaluation_metric": None
        }
        
        param_grid = self._param_grid_validator(param_grid)
        
        try:
            search_result = RandomizedSearchCV(model, param_grid, n_iter=n_trials, scoring=eval_metric, cv=cv, n_jobs=n_jobs, verbose=1).fit(self.X, self.y)

            model_stats['tuned_model'] = search_result.best_estimator_
            model_stats['tuned_model_score'] = self._model_evaluator(search_result.best_estimator_, eval_metric)
            model_stats['tuned_model_evaluation_metric'] = eval_metric
            return model_stats
        
        except Exception as e:
            self.logger.error(f"Error while tuning the model with RandomizedSearchCV, Error: {e}")
            return None
        
    def optuna_search(self,
               model: object,
               param_grid: dict,
               eval_metric: str,
               n_trials: int = 10,
               timeout: Optional[int] = None,
               n_jobs: int = -1) -> Optional[dict]:
        """
        Implements Optuna hyperparameter optimization on the giveen machine learning model

        Parameters
        ----------
        model : object
            The model object that will be tuned.

        param_grid : dict
            The dictionary that contains the hyperparameters and their possible values.

        eval_metric : str
            The evaluation metric that will be used to evaluate the model. It can be one of the following:
            
            * 'r2' for R^2 score
            
            * 'mae' for Mean Absolute Error
            
            * 'mse' for Mean Squared Error
            
            * 'accuracy' for Accuracy
            
            * 'precision' for Precision
            
            * 'recall' for Recall
            
            * 'f1' for F1 score

        n_trials : int, optional (default=100)
            The number of trials. The default is 100.

        timeout : int, optional (default=None)
            The timeout in seconds. The default is None.

        n_jobs : int, optional (default=-1)
            The number of parallel jobs to run. The default is -1.

        Returns
        -------
        model_stats: dict
            Dictionary including tuning information and model:

            * 'tuning_method': The tuning method that is used for the optimization
            
            * 'tuning_param_grid': The hyperparameter grid that is used for the optimization
            
            * 'cv': The number of cross-validation splits
            
            * 'n_jobs': The number of parallel jobs to run
            
            * 'tuned_model': The tuned model object
            
            * 'tuned_model_score': The evaluation metric score of the tuned model
            
            * 'tuned_model_evaluation_metric': The evaluation metric that is used to evaluate the tuned model
        """
        model_stats = {
            "tuning_method": "Optuna",
            "tuning_param_grid": param_grid,
            "cv": None,
            "n_jobs": n_jobs,
            "tuned_model": None,
            "tuned_model_score": None,
            "tuned_model_evaluation_metric": None
        }

        study_direction = "maximize" if eval_metric in ['r2', 'accuracy', 'precision', 'recall', 'f1'] else "minimize"

        def objective(trial):
            """
            Brief explanation of the objective function usage here:

            * The objective function is used to optimize the hyperparameters of the model with Optuna
            * It's called in each trial and returns the evaluation metric score of the model with the current hyperparameters
            
            * In our scenario, we have to make the param grid dynamic for every model, so that:
                * We have to get the first element of the param_values to understand the data type of the hyperparameter
                * Then, we have to use the appropriate Optuna function to get the hyperparameter value for the current trial
            """
            params = {}
            for param_name, param_values in param_grid.items():
                first_element = param_values[0]

                if isinstance(first_element, str) or isinstance(first_element, bool):
                    param_value = trial.suggest_categorical(param_name, param_values)
                    params[param_name] = param_value

                elif isinstance(first_element, int):
                    param_value = trial.suggest_int(param_name, first_element, param_values[len(param_values) - 1])
                    params[param_name] = param_value

                elif isinstance(first_element, float):
                    param_value = trial.suggest_float(param_name, first_element, param_values[len(param_values) - 1])
                    params[param_name] = param_value

                # TODO: Other types can be added too, e.g. suggest_loguniform, suggest_uniform, suggest_discrete_uniform
                else:
                    info_msg = f"Unsupported data type for Optuna tuning, Please use one of the following data types: 'str', 'bool', 'int', 'float', but found {type(first_element)}"
                    self.logger(info_msg)
            
            test_model = type(model)()
            test_model.set_params(**params)
            
            # Train the model
            test_model.fit(self.X_train, self.y_train)
            
            score = self._model_evaluator(test_model, eval_metric)
            
            # Update the best score and best hyperparameters If the current score is better than the best one
            if model_stats['tuned_model_score'] is None or score > model_stats['tuned_model_score']:
                model_stats['tuned_model_score'] = score
                model_stats['tuned_model'] = test_model

            return score
        
        study = optuna.create_study(direction=study_direction)
        study.optimize(objective, n_trials=n_trials, timeout=timeout, n_jobs=n_jobs)
        
        return model_stats