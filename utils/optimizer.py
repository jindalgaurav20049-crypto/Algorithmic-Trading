"""
Advanced Optimization Framework
Supports grid search, genetic algorithms, and Bayesian optimization for >1M parameter combinations
"""

import numpy as np
import pandas as pd
from backtesting import Backtest
import itertools
from concurrent.futures import ProcessPoolExecutor, as_completed
import warnings
warnings.filterwarnings('ignore')

class ParameterOptimizer:
    """
    Optimize strategy parameters using multiple approaches
    """
    
    def __init__(self, data, strategy_class, initial_capital=100000, commission=0.001):
        """
        Initialize optimizer
        
        Args:
            data: OHLCV DataFrame
            strategy_class: Strategy class to optimize
            initial_capital: Starting capital
            commission: Commission rate
        """
        self.data = data
        self.strategy_class = strategy_class
        self.initial_capital = initial_capital
        self.commission = commission
        self.results = []
        
    def grid_search(self, param_grid, max_combinations=None, parallel=True, n_workers=4):
        """
        Exhaustive grid search optimization
        
        Args:
            param_grid: Dictionary of parameter ranges
            max_combinations: Maximum combinations to test (None = all)
            parallel: Use parallel processing
            n_workers: Number of parallel workers
            
        Returns:
            DataFrame: Results sorted by performance
        """
        print(f"Starting grid search optimization...")
        print(f"Parameter ranges:")
        for key, values in param_grid.items():
            print(f"  {key}: {len(values)} values")
        
        # Generate all combinations
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        combinations = list(itertools.product(*values))
        
        total_combinations = len(combinations)
        print(f"\nTotal combinations: {total_combinations:,}")
        
        if max_combinations and total_combinations > max_combinations:
            print(f"Limiting to {max_combinations:,} random combinations")
            np.random.shuffle(combinations)
            combinations = combinations[:max_combinations]
        
        # Run backtests
        if parallel:
            results = self._parallel_backtest(combinations, keys, n_workers)
        else:
            results = self._sequential_backtest(combinations, keys)
        
        # Convert to DataFrame
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('annualized_return', ascending=False)
        
        self.results = results_df
        return results_df
    
    def _sequential_backtest(self, combinations, param_keys):
        """Run backtests sequentially"""
        results = []
        total = len(combinations)
        
        for i, combo in enumerate(combinations):
            if (i + 1) % 100 == 0:
                print(f"Progress: {i+1}/{total} ({100*(i+1)/total:.1f}%)")
            
            params = dict(zip(param_keys, combo))
            result = self._run_single_backtest(params)
            
            if result:
                results.append(result)
        
        return results
    
    def _parallel_backtest(self, combinations, param_keys, n_workers):
        """Run backtests in parallel"""
        results = []
        total = len(combinations)
        completed = 0
        
        with ProcessPoolExecutor(max_workers=n_workers) as executor:
            # Submit all tasks
            futures = []
            for combo in combinations:
                params = dict(zip(param_keys, combo))
                future = executor.submit(self._run_single_backtest, params)
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                    
                    completed += 1
                    if completed % 100 == 0:
                        print(f"Progress: {completed}/{total} ({100*completed/total:.1f}%)")
                except Exception as e:
                    print(f"Error in backtest: {e}")
        
        return results
    
    def _run_single_backtest(self, params):
        """
        Run a single backtest with given parameters
        
        Args:
            params: Dictionary of parameters
            
        Returns:
            dict: Backtest results
        """
        try:
            # Set strategy parameters
            for key, value in params.items():
                setattr(self.strategy_class, key, value)
            
            # Run backtest
            bt = Backtest(self.data, self.strategy_class, 
                         cash=self.initial_capital, 
                         commission=self.commission,
                         exclusive_orders=True)
            
            stats = bt.run()
            
            # Extract metrics
            result = params.copy()
            result['final_equity'] = float(stats['Equity Final [$]'])
            result['total_return'] = float(stats['Return [%]'])
            result['annualized_return'] = float(stats.get('Return (Ann.) [%]', 0))
            result['sharpe_ratio'] = float(stats.get('Sharpe Ratio', 0))
            result['max_drawdown'] = float(stats.get('Max. Drawdown [%]', 0))
            result['win_rate'] = float(stats.get('Win Rate [%]', 0))
            result['num_trades'] = int(stats.get('# Trades', 0))
            result['avg_trade'] = float(stats.get('Avg. Trade [%]', 0))
            
            # Calculate trades per year
            duration_years = (self.data.index[-1] - self.data.index[0]).days / 365.25
            result['trades_per_year'] = result['num_trades'] / duration_years if duration_years > 0 else 0
            
            return result
            
        except Exception as e:
            # Skip failed backtests
            return None
    
    def genetic_optimization(self, param_ranges, population_size=100, generations=50, 
                           mutation_rate=0.1, crossover_rate=0.7):
        """
        Genetic algorithm optimization
        
        Args:
            param_ranges: Dict with parameter names and (min, max, type) tuples
            population_size: Size of population
            generations: Number of generations
            mutation_rate: Probability of mutation
            crossover_rate: Probability of crossover
            
        Returns:
            DataFrame: Best results
        """
        print(f"Starting genetic algorithm optimization...")
        print(f"Population: {population_size}, Generations: {generations}")
        
        # Initialize population
        population = self._initialize_population(param_ranges, population_size)
        
        best_ever = None
        best_fitness = -np.inf
        
        for gen in range(generations):
            print(f"\nGeneration {gen+1}/{generations}")
            
            # Evaluate fitness
            fitness_scores = []
            for individual in population:
                result = self._run_single_backtest(individual)
                if result:
                    fitness = result['annualized_return']
                    fitness_scores.append(fitness)
                    
                    if fitness > best_fitness:
                        best_fitness = fitness
                        best_ever = result
                else:
                    fitness_scores.append(-np.inf)
            
            print(f"  Best fitness: {max(fitness_scores):.2f}%")
            print(f"  Mean fitness: {np.mean([f for f in fitness_scores if f > -np.inf]):.2f}%")
            
            # Selection
            selected = self._tournament_selection(population, fitness_scores, population_size)
            
            # Crossover and mutation
            new_population = []
            for i in range(0, len(selected), 2):
                parent1 = selected[i]
                parent2 = selected[i+1] if i+1 < len(selected) else selected[0]
                
                if np.random.rand() < crossover_rate:
                    child1, child2 = self._crossover(parent1, parent2, param_ranges)
                else:
                    child1, child2 = parent1.copy(), parent2.copy()
                
                if np.random.rand() < mutation_rate:
                    child1 = self._mutate(child1, param_ranges)
                if np.random.rand() < mutation_rate:
                    child2 = self._mutate(child2, param_ranges)
                
                new_population.extend([child1, child2])
            
            population = new_population[:population_size]
        
        print(f"\nBest solution found:")
        print(f"  Parameters: {best_ever}")
        print(f"  Annualized Return: {best_fitness:.2f}%")
        
        return pd.DataFrame([best_ever])
    
    def _initialize_population(self, param_ranges, size):
        """Initialize random population"""
        population = []
        for _ in range(size):
            individual = {}
            for param, (min_val, max_val, param_type) in param_ranges.items():
                if param_type == 'int':
                    individual[param] = np.random.randint(min_val, max_val + 1)
                elif param_type == 'float':
                    individual[param] = np.random.uniform(min_val, max_val)
                elif param_type == 'choice':
                    individual[param] = np.random.choice([min_val, max_val])
            population.append(individual)
        return population
    
    def _tournament_selection(self, population, fitness_scores, size, tournament_size=3):
        """Tournament selection"""
        selected = []
        for _ in range(size):
            tournament = np.random.choice(len(population), tournament_size, replace=False)
            winner = tournament[np.argmax([fitness_scores[i] for i in tournament])]
            selected.append(population[winner].copy())
        return selected
    
    def _crossover(self, parent1, parent2, param_ranges):
        """Single-point crossover"""
        keys = list(parent1.keys())
        point = np.random.randint(1, len(keys))
        
        child1 = {}
        child2 = {}
        
        for i, key in enumerate(keys):
            if i < point:
                child1[key] = parent1[key]
                child2[key] = parent2[key]
            else:
                child1[key] = parent2[key]
                child2[key] = parent1[key]
        
        return child1, child2
    
    def _mutate(self, individual, param_ranges):
        """Random mutation"""
        mutated = individual.copy()
        param = np.random.choice(list(param_ranges.keys()))
        min_val, max_val, param_type = param_ranges[param]
        
        if param_type == 'int':
            mutated[param] = np.random.randint(min_val, max_val + 1)
        elif param_type == 'float':
            mutated[param] = np.random.uniform(min_val, max_val)
        elif param_type == 'choice':
            mutated[param] = np.random.choice([min_val, max_val])
        
        return mutated
