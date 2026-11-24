# Developers' Guide: Development/Testing Configuration

This documentation is NOT intended for regular users, such as researchers or data scientists.

## Environment Variables

These are designed to override configurations specifically related to how the CLI/library operates.

### `DNASTACK_AUTH_LOG_LEVEL`       
| Interpreted Type | Default Value |
|------------------|---------------|
| `str`            | `WARNING`     |

The default log level for authenticators. You can choose either `DEBUG`, `INFO`, `WARNING`, or `ERROR`. This will overrides the default log level or the log level defined by `DNASTACK_LOG_LEVEL` or the log level as the result of the debug mode.       |

### `DNASTACK_CONFIG_FILE`          
| Interpreted Type | Default Value                    |
|------------------|----------------------------------|
| `str`            | `${HOME}/.dnastack/config .yaml` |

Override the default location of the configuration file. For testing, please define this variable.                                                                                                                                                         |

### `DNASTACK_DEBUG`                
| Interpreted Type | Default Value |
|------------------|---------------|
| `bool`           | `false`       |

Enable the global debug mode for the CLI/library. When the debug mode is enabled, the library will override the default log level (`DNASTACK_LOG_LEVEL`) to `DEBUG`. Debug mode does not enable http.client wire tracing, which prints request and response bodies. |

### `DNASTACK_DEV`                  
| Interpreted Type | Default Value |
|------------------|---------------|
| `bool`           | `false`       |

Display hidden command lines, e.g., low-level commands                                                                                                                                                                                                     |

### `DNASTACK_LOG_LEVEL`            
| Interpreted Type | Default Value |
|------------------|---------------|
| `str`            | `WARNING`     |

The default log level. You can choose either `DEBUG`, `INFO`, `WARNING`, or `ERROR`. Please note that setting to `DEBUG` WILL NOT enable the debug mode (`DNASTACK_DEBUG`).                                                                                |

### `DNASTACK_SESSION_DIR`          
| Interpreted Type | Default Value                 |
|------------------|-------------------------------|
| `str`            | `${HOME}/.dnastack/sessions/` |

Override the default location of the session files. For testing, please define this variable.                                                                                                                                                              |

### `DNASTACK_SHOW_LIST_ITEM_INDEX` 
| Interpreted Type | Default Value |
|------------------|---------------|
| `bool`           | `false`       |

Allow the CLI to show the index number of the list items in the output. This feature is automatically disabled when the CLI runs in the non-interactive shell.                                                                                             |
